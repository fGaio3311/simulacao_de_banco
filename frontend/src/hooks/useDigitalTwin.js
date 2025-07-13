import { useState, useEffect, useCallback } from 'react';
import api from '../api';

export function useDigitalTwin() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetch = useCallback(async () => {
    setLoading(true);
    const { data } = await api.get('/digital-twin/summary');
    setSummary(data);
    setLoading(false);
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  return { summary, loading, refetch: fetch };
}
