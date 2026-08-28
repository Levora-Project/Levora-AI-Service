-- CreateTable
CREATE TABLE "sources" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "name" TEXT NOT NULL,
    "display_name" TEXT NOT NULL,
    "base_url" TEXT NOT NULL,
    "api_endpoint" TEXT NOT NULL,
    "method" TEXT NOT NULL DEFAULT 'wordpress_api',
    "pagination_config" JSONB NOT NULL DEFAULT '{}',
    "field_mapping" JSONB NOT NULL DEFAULT '{}',
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "scrape_frequency" TEXT DEFAULT 'daily',
    "last_scraped_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "sources_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "raw_opportunities" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "source_id" UUID NOT NULL,
    "raw_payload" JSONB NOT NULL DEFAULT '{}',
    "source_url" TEXT NOT NULL,
    "scraped_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "error_message" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "raw_opportunities_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "cleaned_opportunities" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "raw_opportunity_id" UUID,
    "source_id" UUID NOT NULL,
    "title" TEXT NOT NULL,
    "organization" TEXT,
    "opportunity_type" TEXT,
    "description" TEXT,
    "eligibility" JSONB NOT NULL DEFAULT '{}',
    "location" TEXT,
    "is_remote" BOOLEAN NOT NULL DEFAULT false,
    "funding_type" TEXT,
    "deadline" TIMESTAMP(3),
    "application_url" TEXT,
    "source_url" TEXT NOT NULL,
    "country" TEXT,
    "study_levels" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "fields_of_study" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "status" TEXT NOT NULL DEFAULT 'pending',
    "error_message" TEXT,
    "content_hash" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "cleaned_opportunities_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "match_scores" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "user_id" UUID NOT NULL,
    "opportunity_id" UUID NOT NULL,
    "score_pct" INTEGER NOT NULL,
    "score_breakdown" JSONB NOT NULL DEFAULT '{}',
    "calculation_version" INTEGER NOT NULL DEFAULT 1,
    "calculated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "match_scores_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "api_keys" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "key" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "last_used_at" TIMESTAMP(3),
    "expires_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "api_keys_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "sources_name_key" ON "sources"("name");

-- CreateIndex
CREATE UNIQUE INDEX "cleaned_opportunities_raw_opportunity_id_key" ON "cleaned_opportunities"("raw_opportunity_id");

-- CreateIndex
CREATE UNIQUE INDEX "match_scores_user_id_opportunity_id_key" ON "match_scores"("user_id", "opportunity_id");

-- CreateIndex
CREATE UNIQUE INDEX "api_keys_key_key" ON "api_keys"("key");

-- AddForeignKey
ALTER TABLE "raw_opportunities" ADD CONSTRAINT "raw_opportunities_source_id_fkey" FOREIGN KEY ("source_id") REFERENCES "sources"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "cleaned_opportunities" ADD CONSTRAINT "cleaned_opportunities_raw_opportunity_id_fkey" FOREIGN KEY ("raw_opportunity_id") REFERENCES "raw_opportunities"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "cleaned_opportunities" ADD CONSTRAINT "cleaned_opportunities_source_id_fkey" FOREIGN KEY ("source_id") REFERENCES "sources"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "match_scores" ADD CONSTRAINT "match_scores_opportunity_id_fkey" FOREIGN KEY ("opportunity_id") REFERENCES "cleaned_opportunities"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
