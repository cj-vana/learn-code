/*
 * TanStack Query bindings over `apiClient`. Components consume these hooks and
 * never touch `fetch` or the client directly, so the `/api/v1` surface stays in
 * one place and query keys stay consistent.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import type {
  ExerciseSubmissionRequest,
  PlaygroundRunRequest,
  PublicRunRequest,
  QuizAnswerRequest,
  ReviewRequest,
  TimedSessionRequest,
} from '../contracts';

export const queryKeys = {
  health: ['health'] as const,
  plan: ['plan'] as const,
  progress: ['progress'] as const,
  contentList: ['content'] as const,
  contentDetail: (id: string) => ['content', id] as const,
  lessonDetail: (id: string) => ['lesson', id] as const,
  quizDetail: (id: string) => ['quiz', id] as const,
  paths: ['paths'] as const,
  pathDetail: (id: string) => ['paths', id] as const,
};

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: ({ signal }) => apiClient.health(signal),
    refetchInterval: 20_000,
    retry: false,
  });
}

export function useUpdateStatus() {
  return useQuery({
    queryKey: ['update'] as const,
    queryFn: ({ signal }) => apiClient.updateStatus(signal),
    staleTime: 60 * 60 * 1000,
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

export function useLessonDetail(lessonId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.lessonDetail(lessonId ?? ''),
    queryFn: ({ signal }) => apiClient.getLesson(lessonId as string, signal),
    enabled: Boolean(lessonId),
  });
}

export function useQuizDetail(quizId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.quizDetail(quizId ?? ''),
    queryFn: ({ signal }) => apiClient.getQuiz(quizId as string, signal),
    enabled: Boolean(quizId),
  });
}

export function useCompleteLesson() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (lessonId: string) => apiClient.completeLesson(lessonId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.plan });
      void queryClient.invalidateQueries({ queryKey: queryKeys.progress });
    },
  });
}

export function usePaths() {
  return useQuery({
    queryKey: queryKeys.paths,
    queryFn: ({ signal }) => apiClient.listPaths(signal),
  });
}

export function usePathDetail(pathId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.pathDetail(pathId ?? ''),
    queryFn: ({ signal }) => apiClient.getPath(pathId as string, signal),
    enabled: Boolean(pathId),
  });
}

export function useEnrollPath() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (pathId: string) => apiClient.enrollPath(pathId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.paths });
      void queryClient.invalidateQueries({ queryKey: queryKeys.plan });
    },
  });
}

export function useUnenrollPath() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (pathId: string) => apiClient.unenrollPath(pathId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.paths });
      void queryClient.invalidateQueries({ queryKey: queryKeys.plan });
    },
  });
}

export function useStartTimedSession() {
  return useMutation({
    mutationFn: (body: TimedSessionRequest) => apiClient.startTimedSession(body),
  });
}

export function useAnswerQuiz() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: QuizAnswerRequest) => apiClient.answerQuiz(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.plan });
      void queryClient.invalidateQueries({ queryKey: queryKeys.progress });
    },
  });
}
