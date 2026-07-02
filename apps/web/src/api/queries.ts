/*
 * TanStack Query bindings over `apiClient`. Components consume these hooks and
 * never touch `fetch` or the client directly, so the `/api/v1` surface stays in
 * one place and query keys stay consistent.
 */

import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from './client';
import type {
  ExerciseSubmissionRequest,
  PlaygroundRunRequest,
  PublicRunRequest,
  ReviewRequest,
} from '../contracts';

export const queryKeys = {
  health: ['health'] as const,
  plan: ['plan'] as const,
  progress: ['progress'] as const,
  contentList: ['content'] as const,
  contentDetail: (id: string) => ['content', id] as const,
};

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: ({ signal }) => apiClient.health(signal),
    refetchInterval: 20_000,
    retry: false,
  });
}

export function usePlan() {
  return useQuery({
    queryKey: queryKeys.plan,
    queryFn: ({ signal }) => apiClient.getPlan(signal),
  });
}

export function useProgress() {
  return useQuery({
    queryKey: queryKeys.progress,
    queryFn: ({ signal }) => apiClient.getProgress(signal),
  });
}

export function useContentList() {
  return useQuery({
    queryKey: queryKeys.contentList,
    queryFn: ({ signal }) => apiClient.listContent(signal),
  });
}

export function useContentDetail(exerciseId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.contentDetail(exerciseId ?? ''),
    queryFn: ({ signal }) => apiClient.getContent(exerciseId as string, signal),
    enabled: Boolean(exerciseId),
  });
}

export function useRunExercise() {
  return useMutation({
    mutationFn: (body: PublicRunRequest) => apiClient.runExercise(body),
  });
}

export function useSubmitExercise() {
  return useMutation({
    mutationFn: (body: ExerciseSubmissionRequest) => apiClient.submitExercise(body),
  });
}

export function useRunPlayground() {
  return useMutation({
    mutationFn: (body: PlaygroundRunRequest) => apiClient.runPlayground(body),
  });
}

export function useRequestReview() {
  return useMutation({
    mutationFn: (body: ReviewRequest) => apiClient.requestReview(body),
  });
}
