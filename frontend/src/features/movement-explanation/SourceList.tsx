import type { Source } from "../../shared/types/explanation";

export function SourceList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) {
    return <p className="empty-state">표시할 출처가 없습니다.</p>;
  }

  return (
    <ul className="source-list">
      {sources.map((source) => (
        <li key={source.id} className="source-list__item">
          <a href={source.url} target="_blank" rel="noreferrer">
            {source.title}
          </a>
          <div className="empty-state">
            {source.publisher} · {source.published_at}
          </div>
        </li>
      ))}
    </ul>
  );
}
