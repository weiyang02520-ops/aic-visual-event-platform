import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// Design-system CSS must load before page CSS so page rules win on equal specificity.
import "./design/tokens.css";
import "./design/base.css";
import "./design/ui.css";
import App from "./app/App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
