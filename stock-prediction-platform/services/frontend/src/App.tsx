import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Suspense, lazy } from "react";
import { ErrorBoundary } from "react-error-boundary";
import QueryProvider from "./providers/QueryProvider";
import Layout from "./components/layout/Layout";
import { LoadingSpinner } from "./components/ui";
import ErrorFallback from "./components/ui/ErrorFallback";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Models = lazy(() => import("./pages/Models"));
const Forecasts = lazy(() => import("./pages/Forecasts"));
const Drift = lazy(() => import("./pages/Drift"));
const Backtest = lazy(() => import("./pages/Backtest"));
const Analytics = lazy(() => import("./pages/Analytics"));
const Search = lazy(() => import("./pages/Search"));

export default function App() {
  return (
    <QueryProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route
              path="dashboard"
              element={
                <ErrorBoundary FallbackComponent={ErrorFallback}>
                  <Suspense fallback={<LoadingSpinner />}>
                    <Dashboard />
                  </Suspense>
                </ErrorBoundary>
              }
            />
            <Route
              path="models"
              element={
                <ErrorBoundary FallbackComponent={ErrorFallback}>
                  <Suspense fallback={<LoadingSpinner />}>
                    <Models />
                  </Suspense>
                </ErrorBoundary>
              }
            />
            <Route
              path="forecasts"
              element={
                <ErrorBoundary FallbackComponent={ErrorFallback}>
                  <Suspense fallback={<LoadingSpinner />}>
                    <Forecasts />
                  </Suspense>
                </ErrorBoundary>
              }
            />
            <Route
              path="drift"
              element={
                <ErrorBoundary FallbackComponent={ErrorFallback}>
                  <Suspense fallback={<LoadingSpinner />}>
                    <Drift />
                  </Suspense>
                </ErrorBoundary>
              }
            />
            <Route
              path="backtest"
              element={
                <ErrorBoundary FallbackComponent={ErrorFallback}>
                  <Suspense fallback={<LoadingSpinner />}>
                    <Backtest />
                  </Suspense>
                </ErrorBoundary>
              }
            />
            <Route
              path="analytics"
              element={
                <ErrorBoundary FallbackComponent={ErrorFallback}>
                  <Suspense fallback={<LoadingSpinner />}>
                    <Analytics />
                  </Suspense>
                </ErrorBoundary>
              }
            />
            <Route
              path="search"
              element={
                <ErrorBoundary FallbackComponent={ErrorFallback}>
                  <Suspense fallback={<LoadingSpinner />}>
                    <Search />
                  </Suspense>
                </ErrorBoundary>
              }
            />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryProvider>
  );
}
