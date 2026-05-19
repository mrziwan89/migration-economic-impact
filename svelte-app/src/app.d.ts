declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace App {
    // interface Error {}
    // interface Locals {}
    // interface PageData {}
    // interface PageState {}
    // interface Platform {}
  }

  interface Window {
    Plotly: PlotlyStatic;
  }

  interface PlotlyStatic {
    newPlot(
      target: string | HTMLElement,
      data: unknown[],
      layout?: Record<string, unknown>,
      config?: Record<string, unknown>
    ): Promise<unknown>;
    purge(target: string | HTMLElement): void;
    Plots: { resize(target: string | HTMLElement): void };
  }
}

export {};
