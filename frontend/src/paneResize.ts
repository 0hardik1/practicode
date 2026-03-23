import type { PointerEvent as ReactPointerEvent } from "react";

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

export function startPaneResize(
  event: ReactPointerEvent<HTMLElement>,
  container: HTMLElement | null,
  axis: "x" | "y",
  onChange: (nextPercentage: number) => void,
  minPercentage: number,
  maxPercentage: number,
) {
  if (!container) {
    return;
  }

  event.preventDefault();

  const rect = container.getBoundingClientRect();
  const totalSize = axis === "x" ? rect.width : rect.height;
  if (totalSize <= 0) {
    return;
  }

  document.body.style.userSelect = "none";
  document.body.style.cursor = axis === "x" ? "col-resize" : "row-resize";

  const handleMove = (moveEvent: PointerEvent) => {
    const offset =
      axis === "x" ? moveEvent.clientX - rect.left : moveEvent.clientY - rect.top;
    const nextPercentage = clamp((offset / totalSize) * 100, minPercentage, maxPercentage);
    onChange(nextPercentage);
  };

  const stopDragging = () => {
    document.body.style.userSelect = "";
    document.body.style.cursor = "";
    window.removeEventListener("pointermove", handleMove);
    window.removeEventListener("pointerup", stopDragging);
  };

  window.addEventListener("pointermove", handleMove);
  window.addEventListener("pointerup", stopDragging);
}

