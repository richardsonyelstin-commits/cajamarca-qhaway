"""TF-IDF reproducible y agrupación temporal acotada para objetos contractuales."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import pairwise
from typing import Protocol

from cajamarca_qhaway.capabilities.red_flags_engine.catalog import uit_value
from cajamarca_qhaway.models import ProcurementRecord, RedFlag, compute_red_flag_id

STOPWORDS = frozenset(['de', 'del', 'la', 'las', 'el', 'los', 'y', 'para', 'por', 'en', 'un', 'una', 'al', 'con', 'servicio', 'orden', 'compra', 'contratacion'])
SYNONYMS: dict[str, str] = {'arrendamiento': 'alquiler', 'arrendar': 'alquiler', 'alquilamiento': 'alquiler',
            'retroexcavadoras': 'retroexcavadora', 'tractores': 'tractor', 'maquinas': 'maquina'}


def tokens(text: str) -> list[str]:
    normalized = ''.join(c for c in unicodedata.normalize('NFKD', text.casefold())
                         if not unicodedata.combining(c))
    words: list[str] = re.findall(r'[a-z]{3,}', normalized)
    return [SYNONYMS.get(word, word) for word in words
            if word not in STOPWORDS]


class Vectorizer(Protocol):
    def transform(self, texts: Sequence[str]) -> list[dict[str, float]]: ...


class TfidfVectorizer:
    version = 'qhaway-tfidf-1'

    def transform(self, texts: Sequence[str]) -> list[dict[str, float]]:
        documents: list[Counter[str]] = []
        frequency: Counter[str] = Counter()
        for text in texts:
            words = tokens(text)
            features: Counter[str] = Counter('w:' + word for word in words)
            features.update('b:' + a + ' ' + b for a, b in pairwise(words))
            features.update('c:' + word[i:i+3] for word in words for i in range(len(word)-2))
            documents.append(features)
            frequency.update(features.keys())
        vectors: list[dict[str, float]] = []
        for counts in documents:
            vector = {key: (1 + math.log(value)) * (1 + math.log((len(texts)+1)/(frequency[key]+1)))
                      * (0.15 if key.startswith('c:') else 1)
                      for key, value in counts.items()}
            norm = math.sqrt(sum(value*value for value in vector.values()))
            vectors.append({key: value/norm for key, value in vector.items()} if norm else {})
        return vectors


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    return min(1.0, max(0.0, sum(value * right.get(key, 0.0) for key, value in left.items())))


def equipment_rental(text: str) -> bool:
    words = set(tokens(text))
    heavy = {'retroexcavadora', 'excavadora', 'tractor', 'motoniveladora', 'volquete',
             'cargador', 'rodillo', 'maquinaria'}
    rental = 'alquiler' in words or ('horas' in words and 'maquina' in words) or 'hora' in words and 'maquina' in words
    return rental and bool(words & heavy)


def description(record: ProcurementRecord) -> str:
    tender = record.raw_payload.get('tender', {})
    parts = [record.title]
    if isinstance(tender, dict):
        parts.append(str(tender.get('description') or ''))
        parts.extend(str(item.get('description') or '') for item in tender.get('items', [])
                     if isinstance(item, dict))
    return ' '.join(parts)


@dataclass(frozen=True, slots=True)
class Observation:
    identifier: str
    entity_id: str
    supplier_ruc: str
    amount: float
    text: str
    when: datetime
    source: str
    retrieved_at: datetime
    independent_source: bool = False


def splitting_flags(
    records: Sequence[ProcurementRecord], now: datetime,
    official_date: Callable[[ProcurementRecord], datetime | None],
    vectorizer: Vectorizer | None = None,
) -> list[RedFlag]:
    observations = []
    for record in records:
        when = official_date(record)
        if when is None or not record.supplier_ruc:
            continue
        observations.append(Observation(record.procurement_id, record.entity_id, record.supplier_ruc,
            record.awarded_amount or 0, description(record), when, record.source, record.retrieved_at))
    return observation_flags(observations, now, vectorizer)


def observation_flags(observations: Sequence[Observation], now: datetime,
                      vectorizer: Vectorizer | None = None) -> list[RedFlag]:
    grouped: dict[tuple[str, int, str], list[Observation]] = defaultdict(list)
    for record in observations:
        when = record.when
        try:
            limit = 8 * uit_value(when.year)
        except ValueError:
            continue
        if not math.isfinite(record.amount) or not 0 < record.amount < limit:
            continue
        grouped[(record.entity_id, when.year, record.supplier_ruc)].append(record)
    results: list[RedFlag] = []
    for (entity_id, year, supplier), entries in sorted(grouped.items()):
        entries.sort(key=lambda item: (item.when, item.identifier))
        vectors = (vectorizer or TfidfVectorizer()).transform([record.text for record in entries])
        # Bloqueo por términos compartidos y representantes deterministas, no todos los pares.
        leaders: dict[str, set[int]] = defaultdict(set)
        clusters: dict[int, list[int]] = {}
        for index, vector in enumerate(vectors):
            words = {key for key in vector if key.startswith('w:')}
            candidates = sorted({leader for word in words for leader in leaders[word]})
            matches = [(cosine(vectors[leader], vector), leader) for leader in candidates]
            match = max(matches, default=(0.0, index))
            leader = match[1] if match[0] >= 0.78 else index
            clusters.setdefault(leader, []).append(index)
            if leader == index:
                for word in words:
                    leaders[word].add(leader)
        for leader, members in clusters.items():
            start = 0
            total = 0.0
            best: tuple[int, int, float] | None = None
            for end, index in enumerate(members):
                total += entries[index].amount
                while entries[index].when - entries[members[start]].when > timedelta(days=90):
                    total -= entries[members[start]].amount
                    start += 1
                if end > start and total > 8 * uit_value(year) and (best is None or total > best[2]):
                    best = (start, end, total)
            if best is None:
                continue
            start, end, total = best
            selected = members[start:end+1]
            chosen = [entries[i] for i in selected]
            similarity = min(cosine(vectors[leader], vectors[i]) for i in selected)
            ids = sorted(record.identifier for record in chosen)
            retrieved = max(record.retrieved_at for record in chosen)
            results.append(RedFlag(
            red_flag_id=compute_red_flag_id('contract-splitting-orders', entity_id+':'+supplier+':'+','.join(ids), str(year)),
            indicator_code='contract-splitting-orders',
            formula_description=f'Suma de órdenes individuales menores a 8 UIT de {year}, mismo comprador y RUC, '
                'en hasta 90 días; similitud coseno TF-IDF >= 0.78. Candidato a revisión, no prueba de fraccionamiento.',
            threshold_value={'total_pen_exclusive': 8*uit_value(year), 'cosine_min': 0.78, 'days_max': 90},
            observed_value={'total_pen': total, 'cosine_similarity': round(similarity, 6),
                            'count': len(chosen), 'vectorizer_version': TfidfVectorizer.version},
            procurement_ids=sorted(record.identifier for record in chosen if not record.independent_source),
            source_evidence_ids=sorted(record.identifier for record in chosen if record.independent_source),
            evidence_source=chosen[0].source,
            retrieved_at=retrieved, generated_at=now,
            ))
    return results
