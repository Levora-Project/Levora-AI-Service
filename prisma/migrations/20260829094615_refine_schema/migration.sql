-- DropForeignKey
ALTER TABLE "cleaned_opportunities" DROP CONSTRAINT IF EXISTS "cleaned_opportunities_raw_opportunity_id_fkey";

-- DropForeignKey
ALTER TABLE "cleaned_opportunities" DROP CONSTRAINT IF EXISTS "cleaned_opportunities_source_id_fkey";

-- AlterTable cleaned_opportunities
ALTER TABLE "cleaned_opportunities" ALTER COLUMN "raw_opportunity_id" SET NOT NULL,
ALTER COLUMN "source_id" DROP NOT NULL,
ALTER COLUMN "eligibility" DROP NOT NULL,
ALTER COLUMN "eligibility" DROP DEFAULT,
ALTER COLUMN "is_remote" DROP NOT NULL,
ALTER COLUMN "is_remote" DROP DEFAULT,
ALTER COLUMN "status" DROP NOT NULL,
ALTER COLUMN "status" DROP DEFAULT;

-- AlterTable raw_opportunities (make source_url nullable according to schema)
ALTER TABLE "raw_opportunities" ALTER COLUMN "source_url" DROP NOT NULL;

-- AlterTable sources (ensure defaults and correct text types)
ALTER TABLE "sources" ALTER COLUMN "api_endpoint" SET DEFAULT '',
ALTER COLUMN "is_active" SET DEFAULT true,
ALTER COLUMN "scrape_frequency" SET DEFAULT 'daily';

-- AddForeignKey
ALTER TABLE "cleaned_opportunities" ADD CONSTRAINT "cleaned_opportunities_raw_opportunity_id_fkey" FOREIGN KEY ("raw_opportunity_id") REFERENCES "raw_opportunities"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "cleaned_opportunities" ADD CONSTRAINT "cleaned_opportunities_source_id_fkey" FOREIGN KEY ("source_id") REFERENCES "sources"("id") ON DELETE SET NULL ON UPDATE CASCADE;
