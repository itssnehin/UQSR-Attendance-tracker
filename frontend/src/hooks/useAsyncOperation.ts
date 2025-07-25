import { useState, useCallback, useRef, useEffect } from 'react';
interface AsyncState<T = any> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseAsyncOperationOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
  resetOnSuccess?: boolean;
}

interface UseAsyncOperationReturn<T> {
  state: AsyncState<T>;
  execute: (...args: any[]) => Promise<T | undefined>;
  reset: () => void;
  retry: () => Promise<T | undefined>;
}

export function useAsyncOperation<T = any>(
  asyncFunction: (...args: any[]) => Promise<T>,
  options: UseAsyncOperationOptions = {}
): UseAsyncOperationReturn<T> {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const lastArgsRef = useRef<any[]>([]);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const execute = useCallback(
    async (...args: any[]): Promise<T | undefined> => {
      lastArgsRef.current = args;
      
      setState(prev => ({
        ...prev,
        loading: true,
        error: null,
      }));

      try {
        const result = await asyncFunction(...args);
        
        if (mountedRef.current) {
          setState(prev => ({
            ...prev,
            data: result,
            loading: false,
            error: null,
          }));

          if (options.onSuccess) {
            options.onSuccess(result);
          }

          if (options.resetOnSuccess) {
            setTimeout(() => {
              if (mountedRef.current) {
                reset();
              }
            }, 3000);
          }
        }

        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
        
        if (mountedRef.current) {
          setState(prev => ({
            ...prev,
            loading: false,
            error: errorMessage,
          }));

          if (options.onError) {
            options.onError(error instanceof Error ? error : new Error(errorMessage));
          }
        }

        throw error;
      }
    },
    [asyncFunction, options]
  );

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  const retry = useCallback(async (): Promise<T | undefined> => {
    return execute(...lastArgsRef.current);
  }, [execute]);

  return {
    state,
    execute,
    reset,
    retry,
  };
}

export default useAsyncOperation;