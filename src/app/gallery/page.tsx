import { CTASection } from "@/components/sections/cta-section";
import { ComparisonShowcase } from "@/components/sections/comparison-showcase";
import { GalleryGrid } from "@/components/sections/gallery-grid";
import { PageHeader } from "@/components/sections/page-header";
import { Section } from "@/components/ui/section";
import { SectionTitle } from "@/components/ui/section-title";
import { galleryItems } from "@/content/gallery";
import { comparisons } from "@/content/home";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Gallery",
  description:
    "Finished work from the Apex Detailing studio: before and after correction, ceramic coating, paint protection film, interior restoration and paint correction.",
  path: "/gallery",
});

export default function GalleryPage() {
  return (
    <>
      <PageHeader
        eyebrow="Gallery"
        title="Cars that left the studio finished"
        description="A selection of recent work. Every image is from a vehicle that came through our bays — filter by the service you are considering."
        image="/media/gallery/g-13.svg"
      />

      <Section aria-labelledby="compare-gallery-title">
        <SectionTitle
          id="compare-gallery-title"
          eyebrow="Case studies"
          title="Three corrections, handle-dragged"
          description="The clearest way to judge a detailer is the same panel before and after. Drag to compare."
        />
        <div className="mt-14">
          <ComparisonShowcase pairs={comparisons} />
        </div>
      </Section>

      <Section tone="raised" aria-labelledby="grid-title">
        <SectionTitle
          id="grid-title"
          eyebrow="Recent work"
          title="Browse the archive"
          description="Sixteen recent jobs across coating, film, correction and interior work. Select any image to view it larger."
        />
        <GalleryGrid items={galleryItems} className="mt-12" />
      </Section>

      <CTASection
        eyebrow="Your car next"
        title="Book the same treatment"
        description="Tell us what you liked in the gallery and what your car looks like today. We will tell you what it takes to get there."
      />
    </>
  );
}
