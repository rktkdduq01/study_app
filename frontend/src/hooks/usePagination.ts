import { useState, useCallback, useMemo } from 'react';

interface UsePaginationProps {
  totalItems: number;
  itemsPerPage: number;
  initialPage?: number;
}

export const usePagination = ({ 
  totalItems, 
  itemsPerPage, 
  initialPage = 1 
}: UsePaginationProps) => {
  const [currentPage, setCurrentPage] = useState(initialPage);

  const totalPages = useMemo(() => 
    Math.ceil(totalItems / itemsPerPage), 
    [totalItems, itemsPerPage]
  );

  const startIndex = useMemo(() => 
    (currentPage - 1) * itemsPerPage, 
    [currentPage, itemsPerPage]
  );

  const endIndex = useMemo(() => 
    Math.min(startIndex + itemsPerPage, totalItems), 
    [startIndex, itemsPerPage, totalItems]
  );

  const goToPage = useCallback((page: number) => {
    const pageNumber = Math.max(1, Math.min(page, totalPages));
    setCurrentPage(pageNumber);
  }, [totalPages]);

  const nextPage = useCallback(() => {
    goToPage(currentPage + 1);
  }, [currentPage, goToPage]);

  const previousPage = useCallback(() => {
    goToPage(currentPage - 1);
  }, [currentPage, goToPage]);

  const resetPage = useCallback(() => {
    setCurrentPage(1);
  }, []);

  return {
    currentPage,
    totalPages,
    startIndex,
    endIndex,
    hasNextPage: currentPage < totalPages,
    hasPreviousPage: currentPage > 1,
    goToPage,
    nextPage,
    previousPage,
    resetPage,
  };
};