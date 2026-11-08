import { SEARCH_DELAY_MS } from "../constants/timing.js";

export function createPagedSearch(fetchPage) {
  let page = 0;
  let loaded = false;
  let timer = null;

  function newSearch() {
    page = 0;
    fetchPage({ page, append: false });
  }

  return {
    newSearch,
    scheduleSearch() {
      clearTimeout(timer);
      timer = setTimeout(newSearch, SEARCH_DELAY_MS);
    },
    loadMore() {
      page += 1;
      fetchPage({ page, append: true });
    },
    loadOnce() {
      if (!loaded) {
        loaded = true;
        newSearch();
      }
    },
  };
}

export function bindPagedSearch(search, { form, input, filters, moreButton }) {
  form.addEventListener("submit", (event) => event.preventDefault());
  input.addEventListener("input", search.scheduleSearch);
  for (const filter of filters) {
    filter.addEventListener("change", search.newSearch);
  }
  moreButton.addEventListener("click", search.loadMore);
}
