export type ChecklistTag = "positive" | "negative" | "earnings" | "caution" | "neutral";

export interface ChecklistItem {
  id: string;
  tag: ChecklistTag;
  headline: string;
  description: string;
  source_count: number;
  url: string;
}

export interface ChecklistResponse {
  ticker: string;
  date: string;
  total_article_count: number;
  items: ChecklistItem[];
}
