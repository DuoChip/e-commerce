-- Run in SQL Server Management Studio or with sqlcmd.
-- master is a system database. Project tables live in database [ecommerce]
-- and in schema [ecommerce] within that database.

IF DB_ID(N'ecommerce') IS NULL
    EXEC(N'CREATE DATABASE [ecommerce]');
GO

USE [ecommerce];
GO

IF SCHEMA_ID(N'ecommerce') IS NULL
    EXEC(N'CREATE SCHEMA [ecommerce]');
GO

IF OBJECT_ID(N'ecommerce.dim_date', N'U') IS NULL
BEGIN
    CREATE TABLE [ecommerce].[dim_date] (
        [date_key] INT NOT NULL PRIMARY KEY,
        [date] DATE NOT NULL UNIQUE,
        [year] SMALLINT NOT NULL,
        [quarter] TINYINT NOT NULL,
        [month] TINYINT NOT NULL,
        [day] TINYINT NOT NULL
    );
END;
GO

IF OBJECT_ID(N'ecommerce.dim_customer', N'U') IS NULL
BEGIN
    CREATE TABLE [ecommerce].[dim_customer] (
        [customer_key] INT NOT NULL PRIMARY KEY,
        [customer_id] BIGINT NOT NULL UNIQUE,
        [recency_days] INT NULL,
        [frequency] INT NOT NULL,
        [monetary_net] DECIMAL(19, 6) NOT NULL,
        [r_score] TINYINT NOT NULL,
        [f_score] TINYINT NOT NULL,
        [m_score] TINYINT NOT NULL,
        [value_tier] NVARCHAR(20) NOT NULL,
        [status] NVARCHAR(20) NOT NULL,
        [snapshot_date] DATE NOT NULL
    );
END;
GO

IF OBJECT_ID(N'ecommerce.dim_product', N'U') IS NULL
BEGIN
    CREATE TABLE [ecommerce].[dim_product] (
        [product_key] INT NOT NULL PRIMARY KEY,
        [stock_code] NVARCHAR(50) NOT NULL UNIQUE,
        [description] NVARCHAR(255) NOT NULL
    );
END;
GO

IF OBJECT_ID(N'ecommerce.dim_country', N'U') IS NULL
BEGIN
    CREATE TABLE [ecommerce].[dim_country] (
        [country_key] INT NOT NULL PRIMARY KEY,
        [country] NVARCHAR(100) NOT NULL UNIQUE
    );
END;
GO

IF OBJECT_ID(N'ecommerce.fact_transactions', N'U') IS NULL
BEGIN
    CREATE TABLE [ecommerce].[fact_transactions] (
        [transaction_line_key] BIGINT NOT NULL PRIMARY KEY,
        [invoice_no] NVARCHAR(50) NOT NULL,
        [invoice_datetime] DATETIME2(0) NOT NULL,
        [date_key] INT NOT NULL,
        [customer_key] INT NOT NULL,
        [product_key] INT NOT NULL,
        [country_key] INT NOT NULL,
        [transaction_type] NVARCHAR(10) NOT NULL,
        [quantity] INT NOT NULL,
        [unit_price] DECIMAL(19, 6) NOT NULL,
        [gross_sales] DECIMAL(19, 6) NOT NULL,
        [return_amount] DECIMAL(19, 6) NOT NULL,
        [net_sales] DECIMAL(19, 6) NOT NULL,
        CONSTRAINT [CK_fact_transaction_type]
            CHECK ([transaction_type] IN (N'Sale', N'Return')),
        CONSTRAINT [FK_fact_date]
            FOREIGN KEY ([date_key]) REFERENCES [ecommerce].[dim_date]([date_key]),
        CONSTRAINT [FK_fact_customer]
            FOREIGN KEY ([customer_key]) REFERENCES [ecommerce].[dim_customer]([customer_key]),
        CONSTRAINT [FK_fact_product]
            FOREIGN KEY ([product_key]) REFERENCES [ecommerce].[dim_product]([product_key]),
        CONSTRAINT [FK_fact_country]
            FOREIGN KEY ([country_key]) REFERENCES [ecommerce].[dim_country]([country_key])
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_fact_date'
               AND object_id = OBJECT_ID(N'ecommerce.fact_transactions'))
    CREATE INDEX [IX_fact_date] ON [ecommerce].[fact_transactions]([date_key]);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_fact_customer'
               AND object_id = OBJECT_ID(N'ecommerce.fact_transactions'))
    CREATE INDEX [IX_fact_customer] ON [ecommerce].[fact_transactions]([customer_key]);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_fact_product'
               AND object_id = OBJECT_ID(N'ecommerce.fact_transactions'))
    CREATE INDEX [IX_fact_product] ON [ecommerce].[fact_transactions]([product_key]);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_fact_country'
               AND object_id = OBJECT_ID(N'ecommerce.fact_transactions'))
    CREATE INDEX [IX_fact_country] ON [ecommerce].[fact_transactions]([country_key]);
GO
