CREATE DATABASE IF NOT EXISTS price_monitor;
USE price_monitor;

-- Tabel produk: master data produk dari setiap sumber
CREATE TABLE IF NOT EXISTS produk (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    source ENUM('ebay', 'aliexpress') NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    category VARCHAR(255) DEFAULT NULL,
    seller_name VARCHAR(255) DEFAULT NULL,
    seller_rating DECIMAL(3,2) DEFAULT NULL,
    first_seen DATETIME NOT NULL,
    last_seen DATETIME NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE KEY uk_source_source_id (source, source_id),
    INDEX idx_category (category),
    INDEX idx_seller_name (seller_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabel histori harga: setiap fetch menjadi baris baru
CREATE TABLE IF NOT EXISTS histori_harga (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id BIGINT NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    rating DECIMAL(3,2) DEFAULT NULL,
    review_count INT DEFAULT NULL,
    sold_count INT DEFAULT NULL,
    fetched_at DATETIME NOT NULL,
    fetch_batch VARCHAR(36) DEFAULT NULL,
    FOREIGN KEY (product_id) REFERENCES produk(id),
    INDEX idx_product_fetched (product_id, fetched_at),
    INDEX idx_fetched_at (fetched_at),
    INDEX idx_fetch_batch (fetch_batch)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
