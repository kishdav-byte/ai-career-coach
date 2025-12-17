-- Update Single Feature Prices
UPDATE public.products SET price = 6.99 WHERE name IN ('Cover Letter', 'LinkedIn Optimizer', 'The Closer', 'The Inquisitor', 'Value Follow-Up');

-- Update Premium Feature Prices
UPDATE public.products SET price = 12.99 WHERE name = 'Executive Rewrite';
UPDATE public.products SET price = 8.99 WHERE name = '30-60-90 Day Plan';

-- Note: The Bundle remains at 29.99
