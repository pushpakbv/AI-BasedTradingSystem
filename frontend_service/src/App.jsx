import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { PredictionsProvider } from "./context/PredictionsContext";

import Dashboard from "./pages/Dashboard";
import StockDetail from "./pages/StockDetail";

export default function App() {
  return (
    <BrowserRouter>
      <PredictionsProvider>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/stock/:ticker" element={<StockDetail />} />
        </Routes>
      </PredictionsProvider>
    </BrowserRouter>
  );
}