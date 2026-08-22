import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "HYROX Coach",
    short_name: "HYROX Coach",
    description: "Shared HYROX Doubles preparation, grounded in real training data.",
    start_url: "/dashboard",
    display: "standalone",
    background_color: "#0b0d10",
    theme_color: "#0b0d10",
    icons: [
      {
        src: "/icons/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-512-maskable.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
