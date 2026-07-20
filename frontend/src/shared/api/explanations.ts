import { apiRequest } from "./client";
import type {
  MovementExplanationRequest,
  MovementExplanationResponse,
} from "../types/explanation";

export function fetchMovementExplanation(
  request: MovementExplanationRequest,
): Promise<MovementExplanationResponse> {
  return apiRequest<MovementExplanationResponse>("/api/v1/explanations", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
