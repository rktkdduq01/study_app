/**
 * Mock helper utilities for simulating API delays and responses
 */

/**
 * Simulates network delay for mock API calls
 * @param minMs Minimum delay in milliseconds (default: 300)
 * @param maxMs Maximum delay in milliseconds (default: 800)
 */
export const mockDelay = (minMs: number = 300, maxMs: number = 800): Promise<void> => {
  const delay = Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs;
  return new Promise(resolve => setTimeout(resolve, delay));
};

/**
 * Simulates API errors randomly for testing error handling
 * @param errorRate Probability of error (0-1, default: 0)
 * @param errorMessage Custom error message
 */
export const mockError = (errorRate: number = 0, errorMessage: string = 'Mock API Error'): void => {
  if (Math.random() < errorRate) {
    throw new Error(errorMessage);
  }
};

/**
 * Generates random data within a range
 * @param min Minimum value
 * @param max Maximum value
 * @param decimal Whether to include decimals
 */
export const randomInRange = (min: number, max: number, decimal: boolean = false): number => {
  const value = Math.random() * (max - min) + min;
  return decimal ? value : Math.floor(value);
};

/**
 * Randomly picks items from an array
 * @param array Source array
 * @param count Number of items to pick (default: 1)
 */
export const randomPick = <T>(array: T[], count: number = 1): T[] => {
  const shuffled = [...array].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
};

/**
 * Generates a random date within a range
 * @param start Start date
 * @param end End date
 */
export const randomDate = (start: Date, end: Date): Date => {
  return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
};

/**
 * Generates lorem ipsum text
 * @param wordCount Number of words
 */
export const loremIpsum = (wordCount: number): string => {
  const words = [
    'lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit',
    'sed', 'do', 'eiusmod', 'tempor', 'incididunt', 'ut', 'labore', 'et', 'dolore',
    'magna', 'aliqua', 'enim', 'ad', 'minim', 'veniam', 'quis', 'nostrud',
    'exercitation', 'ullamco', 'laboris', 'nisi', 'aliquip', 'ex', 'ea', 'commodo',
    'consequat', 'duis', 'aute', 'irure', 'in', 'reprehenderit', 'voluptate',
    'velit', 'esse', 'cillum', 'fugiat', 'nulla', 'pariatur', 'excepteur', 'sint',
    'occaecat', 'cupidatat', 'non', 'proident', 'sunt', 'culpa', 'qui', 'officia',
    'deserunt', 'mollit', 'anim', 'id', 'est', 'laborum'
  ];
  
  const result: string[] = [];
  for (let i = 0; i < wordCount; i++) {
    result.push(words[Math.floor(Math.random() * words.length)]);
  }
  
  return result.join(' ');
};