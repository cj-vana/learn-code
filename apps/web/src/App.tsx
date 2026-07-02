import { Navigate, Route, Routes } from 'react-router-dom';
import { WorkbenchShell } from './components/WorkbenchShell';
import { LearnRoute } from './routes/LearnRoute';
import { ExerciseRoute } from './routes/ExerciseRoute';
import { LessonRoute } from './routes/LessonRoute';
import { QuizRoute } from './routes/QuizRoute';
import { PathsRoute } from './routes/PathsRoute';
import { PathRoute } from './routes/PathRoute';
import { TimedRoute } from './routes/TimedRoute';
import { PlaygroundRoute } from './routes/PlaygroundRoute';
import { ReviewRoute } from './routes/ReviewRoute';
import { LibraryRoute } from './routes/LibraryRoute';
import { ProgressRoute } from './routes/ProgressRoute';
import { NotFoundRoute } from './routes/NotFoundRoute';

export function App() {
  return (
    <Routes>
      <Route element={<WorkbenchShell />}>
        <Route index element={<Navigate to="/learn" replace />} />
        <Route path="/learn" element={<LearnRoute />} />
        <Route path="/exercise/:id" element={<ExerciseRoute />} />
        <Route path="/lesson/:id" element={<LessonRoute />} />
        <Route path="/quiz/:id" element={<QuizRoute />} />
        <Route path="/paths" element={<PathsRoute />} />
        <Route path="/path/:id" element={<PathRoute />} />
        <Route path="/timed" element={<TimedRoute />} />
        <Route path="/playground" element={<PlaygroundRoute />} />
        <Route path="/review" element={<ReviewRoute />} />
        <Route path="/library" element={<LibraryRoute />} />
        <Route path="/progress" element={<ProgressRoute />} />
        <Route path="*" element={<NotFoundRoute />} />
      </Route>
    </Routes>
  );
}
