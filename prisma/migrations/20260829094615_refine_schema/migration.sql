/*
  Warnings:

  - You are about to drop the column `source_url` on the `raw_opportunities` table. All the data in the column will be lost.
  - You are about to drop the column `is_active` on the `sources` table. All the data in the column will be lost.
  - You are about to drop the column `scrape_frequency` on the `sources` table. All the data in the column will be lost.
  - The `api_endpoint` column on the `sources` table would be dropped and recreated. This will lead to data loss if there is data in the column.
  - Made the column `raw_opportunity_id` on table `cleaned_opportunities` required. This step will fail if there are existing NULL values in that column.

*/
-- DropForeignKey
ALTER TABLE "cleaned_opportunities" DROP CONSTRAINT "cleaned_opportunities_raw_opportunity_id_fkey";

-- DropForeignKey
ALTER TABLE "cleaned_opportunities" DROP CONSTRAINT "cleaned_opportunities_source_id_fkey";

-- AlterTable
ALTER TABLE "cleaned_opportunities" ALTER COLUMN "raw_opportunity_id" SET NOT NULL,
ALTER COLUMN "source_id" DROP NOT NULL,
ALTER COLUMN "eligibility" DROP NOT NULL,
ALTER COLUMN "eligibility" DROP DEFAULT,
ALTER COLUMN "is_remote" DROP NOT NULL,
ALTER COLUMN "is_remote" DROP DEFAULT,
ALTER COLUMN "status" DROP NOT NULL,
ALTER COLUMN "status" DROP DEFAULT;

-- AlterTable
ALTER TABLE "raw_opportunities" DROP COLUMN "source_url";

-- AlterTable
ALTER TABLE "sources" DROP COLUMN "is_active",
DROP COLUMN "scrape_frequency",
DROP COLUMN "api_endpoint",
ADD COLUMN     "api_endpoint" JSONB NOT NULL DEFAULT '{}';

-- AddForeignKey
ALTER TABLE "cleaned_opportunities" ADD CONSTRAINT "cleaned_opportunities_raw_opportunity_id_fkey" FOREIGN KEY ("raw_opportunity_id") REFERENCES "raw_opportunities"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "cleaned_opportunities" ADD CONSTRAINT "cleaned_opportunities_source_id_fkey" FOREIGN KEY ("source_id") REFERENCES "sources"("id") ON DELETE SET NULL ON UPDATE CASCADE;
