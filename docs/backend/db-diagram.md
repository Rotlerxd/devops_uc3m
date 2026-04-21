erDiagram
    %% Relaciones
    users ||--o{ alerts : "crea (1:N)"
    alerts ||--o{ notifications : "genera (1:N)"
    users ||--o{ user_roles : "tiene (M:N)"
    roles ||--o{ user_roles : "pertenece (M:N)"
    information_sources ||--o{ rss_channels : "agrupa (1:N)"
    categories ||--o{ rss_channels : "clasifica (1:N)"

    %% Tablas y Atributos
    users {
        Integer id PK
        String email UK
        String first_name
        String last_name
        String organization
        String password
        Boolean is_verified
    }

    roles {
        Integer id PK
        String name UK
    }

    user_roles {
        Integer user_id PK, FK
        Integer role_id PK, FK
    }

    alerts {
        Integer id PK
        Integer user_id FK
        String name
        String cron_expression
        ARRAY descriptors
        JSON categories
    }

    notifications {
        Integer id PK
        Integer alert_id FK
        String timestamp
        JSON metrics
        String iptc_category
    }

    information_sources {
        Integer id PK
        String name
        String url
    }

    categories {
        Integer id PK
        String name UK
        String source
    }

    rss_channels {
        Integer id PK
        Integer information_source_id FK
        Integer category_id FK
        String url
    }

    stats {
        Integer id PK
        Integer total_news
        Integer total_notifications
        JSON metrics
    }