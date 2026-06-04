"""Places module — Google Places via the WorkWeek SDK gateway.

Calls /api/v1/sdk/places/* endpoints (Widget path — structured, no LLM).
Auth via X-API-Key. Google Places BYOK key resolved at gateway.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workweek.client import WorkWeekClient


class PlacesModule:
    def __init__(self, client: "WorkWeekClient"):
        self._client = client

    def search(self, name: str, lat: float, lon: float) -> dict:
        """Search Google Places for a business by name, biased by lat/lon.

        Args:
            name: Business name to search for (e.g. ``"Corazon Mexicano"``).
            lat: Latitude to bias search around.
            lon: Longitude to bias search around.

        Returns:
            On match::

                {
                    "found": True,
                    "google_name": str,
                    "google_rating": float | None,
                    "google_total_ratings": int,
                    "google_price_level": str | None,
                    "google_address": str,
                    "place_id": str,
                }

            On no match / missing entitlement / upstream error::

                {"found": False}                              # clean miss
                {"found": False, "reason": "not_configured"}  # no entitlement
                {"found": False, "error": "..."}              # upstream error

        Example::

            result = client.places.search(
                name="Corazon Mexicano",
                lat=37.7647,
                lon=-122.4194,
            )
            if result["found"]:
                print(f"{result['google_name']}: {result['google_rating']}★")
        """
        return self._client.get(
            "/api/v1/sdk/places/search",
            params={"name": name, "lat": lat, "lon": lon},
        )

    def details(self, place_id: str) -> dict:
        """Fetch place details (reviews, website, opening hours) by place_id.

        Args:
            place_id: Google Places place_id (from a prior ``search()`` call).

        Returns:
            On success::

                {
                    "found": True,
                    "reviews": [
                        {
                            "author_name": str,
                            "rating": float | None,
                            "text": str,
                            "relative_time_description": str,
                        },
                        ...  # up to 5 reviews
                    ],
                    "website": str | None,
                    "google_maps_url": str | None,
                    "opening_hours": dict,
                }

            On missing entitlement or upstream error::

                {"found": False, ...}

        Reviews are capped at 5 per call; each review ``text`` is capped at
        500 chars. If you need the full Google review text, call the Places
        API directly (which you'd need if you're running your own backend
        anyway — but the SDK keeps it simple for chat/display use cases).

        Example::

            details = client.places.details(result["place_id"])
            for r in details.get("reviews", []):
                print(f"{r['author_name']} ({r['rating']}★): {r['text'][:80]}")
        """
        return self._client.get(f"/api/v1/sdk/places/details/{place_id}")

    def streetview(self, lat: float, lon: float) -> dict:
        """Return a Google Maps Street View deep-link URL for the coordinates.

        This endpoint does NOT call the Google Places API — the URL format is
        a public Google Maps deep-link convention and requires no API key.
        Google handles "no imagery at the exact location" by finding the
        nearest available panorama automatically.

        Args:
            lat: Latitude.
            lon: Longitude.

        Returns::

            {
                "image_url": "",           # future: Street View Static image
                "link_url": "https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}",
            }

        Example::

            sv = client.places.streetview(37.7647, -122.4194)
            # Open sv["link_url"] in a new tab to show Street View.
        """
        return self._client.get(
            "/api/v1/sdk/places/streetview",
            params={"lat": lat, "lon": lon},
        )
