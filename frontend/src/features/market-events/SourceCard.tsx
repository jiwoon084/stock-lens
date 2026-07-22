import type { Source } from "../../shared/types/explanation";

const TYPE_LABEL: Record<string, string> = {
  news: "뉴스",
  disclosure: "공시",
  report: "리포트",
};

interface SourceCardProps {
  source: Source;
}

export function SourceCard({ source }: SourceCardProps) {
  const typeLabel = TYPE_LABEL[source.type] ?? "자료";
  const publishedDate = source.published_at.slice(0, 10);

  return (
    <a className="source-card" href={source.url} target="_blank" rel="noreferrer">
      <div className="source-card__meta">
        <span className={`source-card__type source-card__type--${source.type}`}>{typeLabel}</span>
        <span className="source-card__date">{publishedDate}</span>
      </div>
      <p className="source-card__title">{source.title}</p>
      <ul className="source-card__excerpt">
        {source.summary_lines.map((line, index) => (
          <li key={index}>{line}</li>
        ))}
      </ul>
      <span className="source-card__publisher">{source.publisher}</span>
    </a>
  );
}
