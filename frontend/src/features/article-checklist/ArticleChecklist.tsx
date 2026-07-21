import { ChecklistItemRow } from "./ChecklistItemRow";
import { useArticleChecklist } from "./useArticleChecklist";

interface ArticleChecklistProps {
  ticker: string;
}

export function ArticleChecklist({ ticker }: ArticleChecklistProps) {
  const { checklist, loading, error, checkedIds, toggleChecked } = useArticleChecklist(ticker);

  if (loading) {
    return <p className="empty-state">오늘의 기사를 정리하는 중입니다...</p>;
  }

  if (!checklist) {
    return <div className="error-banner">{error ?? "체크리스트를 불러오지 못했습니다."}</div>;
  }

  const checkedCount = checklist.items.filter((item) => checkedIds.has(item.id)).length;

  return (
    <div className="article-checklist">
      {error && <div className="error-banner">{error}</div>}
      <p className="article-checklist__summary">
        오늘 기사 {checklist.total_article_count}건 → 핵심 이슈 {checklist.items.length}개로 정리했어요
      </p>

      <div className="article-checklist__list">
        {checklist.items.map((item) => (
          <ChecklistItemRow
            key={item.id}
            item={item}
            checked={checkedIds.has(item.id)}
            onToggle={toggleChecked}
          />
        ))}
      </div>

      <p className="article-checklist__footer">
        확인 완료 {checkedCount}/{checklist.items.length} · 어려운 용어는 눌러서 설명 보기
      </p>
    </div>
  );
}
