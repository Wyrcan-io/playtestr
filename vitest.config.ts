import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // PTY integration files compete for ConPTY/native handles when Vitest fans
    // them out. Serial files preserve process-level determinism; individual
    // pure unit suites remain fast and may still use concurrent test cases.
    fileParallelism: false,
  },
});
