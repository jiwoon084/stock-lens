import type { RecommendedMaterial, SourceMetadata } from "../../types/stockAnalysis";

const SOURCE_TYPE_LABEL: Record<SourceMetadata["source_type"], string> = {
  official_disclosure: "공시",
  market_data: "시장 데이터",
  media_report: "뉴스",
};

interface RecommendedMaterialsProps {
  materials: RecommendedMaterial[];
  sources: Record<string, SourceMetadata>;
}

export function RecommendedMaterials({ materials, sources }: RecommendedMaterialsProps) {
  return (
    <section className="analysis-section">
      <h4 className="analysis-section__title">더 읽어볼 자료</h4>

      {materials.length === 0 ? (
        <p className="empty-state">추천할 자료가 아직 충분하지 않아요.</p>
      ) : (
        <ul className="recommended-materials">
          {materials.map((material) => {
            const source = sources[material.source_id];
            return (
              <li key={material.source_id} id={`source-${material.source_id}`} className="recommended-material-card">
                <div className="recommended-material-card__meta">
                  {source && (
                    <span className={`recommended-material-card__type recommended-material-card__type--${source.source_type}`}>
                      {SOURCE_TYPE_LABEL[source.source_type]}
                    </span>
                  )}
                  {source?.published_at && (
                    <span className="recommended-material-card__date">{source.published_at.slice(0, 10)}</span>
                  )}
                </div>

                <p className="recommended-material-card__title">{source?.title ?? "출처 정보를 찾을 수 없어요"}</p>
                <p className="recommended-material-card__description">{material.description}</p>

                {material.information_to_verify.length > 0 && (
                  <ul className="recommended-material-card__topics">
                    {material.information_to_verify.map((topic) => (
                      <li key={topic}>{topic}</li>
                    ))}
                  </ul>
                )}

                <div className="recommended-material-card__footer">
                  {source?.publisher && <span className="recommended-material-card__publisher">{source.publisher}</span>}
                  {source?.url && (
                    <a
                      className="recommended-material-card__link"
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      원문 보기
                    </a>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
