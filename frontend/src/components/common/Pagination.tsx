import React from 'react';
import {
  Box,
  Pagination as MuiPagination,
  Typography,
  Select,
  MenuItem,
  FormControl,
} from '@mui/material';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  startIndex: number;
  endIndex: number;
  onPageChange: (page: number) => void;
  onItemsPerPageChange?: (itemsPerPage: number) => void;
  itemsPerPageOptions?: number[];
}

const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  startIndex,
  endIndex,
  onPageChange,
  onItemsPerPageChange,
  itemsPerPageOptions = [12, 24, 48],
}) => {
  const handlePageChange = (_event: React.ChangeEvent<unknown>, page: number) => {
    onPageChange(page);
  };

  const handleItemsPerPageChange = (event: any) => {
    if (onItemsPerPageChange) {
      onItemsPerPageChange(Number(event.target.value));
      onPageChange(1); // Reset to first page when changing items per page
    }
  };

  if (totalPages <= 1 && !onItemsPerPageChange) {
    return null;
  }

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 2,
        mt: 3,
      }}
    >
      {/* Results Info */}
      <Typography variant="body2" color="text.secondary">
        Showing {startIndex + 1}-{endIndex} of {totalItems} results
      </Typography>

      {/* Pagination Controls */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {onItemsPerPageChange && (
          <FormControl size="small" variant="outlined">
            <Select
              value={itemsPerPage}
              onChange={handleItemsPerPageChange}
              sx={{ minWidth: 70 }}
            >
              {itemsPerPageOptions.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

        {totalPages > 1 && (
          <MuiPagination
            count={totalPages}
            page={currentPage}
            onChange={handlePageChange}
            color="primary"
            shape="rounded"
            showFirstButton
            showLastButton
          />
        )}
      </Box>
    </Box>
  );
};

export default Pagination;