/**
 * Extract error message from axios error or unknown error
 */
export function getErrorMessage(err: unknown): string {
  if (
    err instanceof Error &&
    'response' in err &&
    typeof err.response === 'object' &&
    err.response !== null &&
    'data' in err.response &&
    typeof err.response.data === 'object' &&
    err.response.data !== null &&
    'detail' in err.response.data
  ) {
    return String(err.response.data.detail)
  }
  
  if (err instanceof Error) {
    return err.message
  }
  
  return 'An unexpected error occurred'
}
