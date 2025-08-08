import { createAlova } from 'alova';
import adapterFetch from 'alova/fetch';
import VueHook from 'alova/vue';

const apiBaseUrl = import.meta.env.VITE_BASE_API;
const TIMEOUT_MS = 3 * 60 * 1000;

export const alovaInstance = createAlova({
  statesHook: VueHook,
  timeout: TIMEOUT_MS,
  baseURL: apiBaseUrl,
  requestAdapter: adapterFetch(),
  responded: {
    onSuccess: async (response: Response) => {
      return await response.json();
    }
  }
});
