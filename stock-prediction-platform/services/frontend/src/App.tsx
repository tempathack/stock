import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Suspense, lazy } from "react";
import QueryProvider from "./providers/QueryProvider";
import Layout from "./components/layout/Layout";
import { LoadingSpinner } from "./components/ui";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Models = lazy(() => import("./pages/Models"));
const Forecasts = lazy(() => import("./pages/Forecasts"));
const Drift = lazy(() => import("./pages/Drift"));
const Backtest = lazy(() => import("./pages/Backtest"));

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
                <Suspense fallback={<LoadingSpinner />}>
                  <Dashboard />
                </Suspense>
              }
            />
            <Route
              path="models"
              element={
                <Suspense fallback={<LoadingSpinner />}>
                  <Models />
                </Suspense>
              }
            />
            <Route
              path="forecasts"
              element={
                <Suspense fallback={<LoadingSpinner />}>
                  <Forecasts />
                </Suspense>
              }
            />
            <Route
              path="drift"
              element={
                <Suspense fallback={<LoadingSpinner />}>
                  <Drift />
                </Suspense>
              }
            />
            <Route
              path="backtest"
              element={
                <Suspense fallback={<LoadingSpinner />}>
                  <Backtest />
                </Suspense>
              }
            />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryProvider>
  );
}
