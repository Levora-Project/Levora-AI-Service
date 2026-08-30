
CREATE ROLE levora_main_service WITH LOGIN PASSWORD 'CHANGE_ME_STRONG_PASSWORD';

GRANT CONNECT ON DATABASE postgres TO levora_main_service;
GRANT USAGE ON SCHEMA public TO levora_main_service;

GRANT SELECT ON TABLE public.cleaned_opportunities TO levora_main_service;
GRANT SELECT ON TABLE public.match_scores TO levora_main_service;

REVOKE ALL ON TABLE public.sources FROM levora_main_service;
REVOKE ALL ON TABLE public.raw_opportunities FROM levora_main_service;
REVOKE ALL ON TABLE public.api_keys FROM levora_main_service;

ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM levora_main_service;