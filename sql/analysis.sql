-- Run in SQL Server after sql/star_schema.sql and the five CSV imports.
USE [ecommerce];
GO

SELECT COUNT(*) AS transaction_lines,
       COUNT(DISTINCT CASE WHEN transaction_type = N'Sale' THEN invoice_no END) AS sale_orders,
       ROUND(SUM(gross_sales), 2) AS gross_sales,
       ROUND(SUM(return_amount), 2) AS returns,
       ROUND(SUM(net_sales), 2) AS net_sales
FROM [ecommerce].[fact_transactions];

SELECT d.[year], d.[month],
       COUNT(DISTINCT CASE WHEN f.transaction_type = N'Sale' THEN f.invoice_no END) AS sale_orders,
       ROUND(SUM(f.gross_sales), 2) AS gross_sales,
       ROUND(SUM(f.return_amount), 2) AS returns,
       ROUND(SUM(f.net_sales), 2) AS net_sales
FROM [ecommerce].[fact_transactions] AS f
JOIN [ecommerce].[dim_date] AS d ON f.date_key = d.date_key
GROUP BY d.[year], d.[month]
ORDER BY d.[year], d.[month];

SELECT TOP (10) c.country, ROUND(SUM(f.net_sales), 2) AS net_sales
FROM [ecommerce].[fact_transactions] AS f
JOIN [ecommerce].[dim_country] AS c ON f.country_key = c.country_key
GROUP BY c.country
ORDER BY net_sales DESC;

SELECT TOP (10) p.stock_code, p.description,
       ROUND(SUM(f.net_sales), 2) AS net_sales,
       SUM(f.quantity) AS net_quantity
FROM [ecommerce].[fact_transactions] AS f
JOIN [ecommerce].[dim_product] AS p ON f.product_key = p.product_key
GROUP BY p.product_key, p.stock_code, p.description
ORDER BY net_sales DESC;
