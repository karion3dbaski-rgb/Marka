import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.middleware.error_handler import ApiError
from app.models.ai_job import AIJob
from app.models.brand import Brand

CONTENT_IDEAS_PROMPT = """Sen bir sosyal medya uzmanısın. {brand_name} markası için içerik fikirleri üret.

Marka Bilgisi:
- Sektör: {sector}
- Ton: {tone}
- Hedef Kitle: {target_audience}
- Anahtar Kelimeler: {keywords}

Platform: {platform}

5 farklı içerik fikri üret. Her fikir için:
1. Başlık
2. Kısa açıklama
3. Önerilen format (resim/video/hikaye/reels)

JSON formatında döndür.
"""

POST_PROMPT = """Sen bir sosyal medya içerik yazarısın. Aşağıdaki fikir için {platform} platformu için bir gönderi yaz.

Marka: {brand_name}
Ton: {tone}
Hedef Kitle: {target_audience}
İçerik Fikri: {idea}
Platform Karakteri: {max_chars}

Dikkat edilecekler:
- Türkçe yaz
- Marka tonuna uygun ol
- Etkileşimi artıracak bir çağrı-eyleme ekle
- Platform kurallarına uy

Sadece gönderi metnini döndür, başka açıklama ekleme.
"""

HASHTAG_PROMPT = """{platform} platformu için {topic} konusunda hashtag öner.
Sektör: {sector}
Dil: Türkçe (Türkçe ve İngilizce karışık olabilir)

20 adet hashtag öner, popülerliklerine göre sırala.
Sadece hashtag listesini döndür, # işareti ile.
"""

PLATFORM_LIMITS = {
    "instagram": 2200,
    "twitter": 280,
    "linkedin": 3000,
    "facebook": 63206,
}


class AIService:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def _create_job(self, db: AsyncSession, user_id: Any, brand_id: Any, job_type: str, provider: str) -> AIJob:
        job = AIJob(user_id=user_id, brand_id=brand_id, job_type=job_type, status="processing", provider=provider)
        db.add(job)
        await db.flush()
        return job

    async def _finalize_job(self, job: AIJob, result: dict[str, Any], *, success: bool = True) -> None:
        job.status = "completed" if success else "failed"
        job.result = result
        job.provider = result.get("provider", job.provider)
        job.model_used = result.get("model")
        job.prompt_tokens = result.get("prompt_tokens")
        job.completion_tokens = result.get("completion_tokens")
        job.cost_usd = Decimal(str(result.get("cost_usd", "0")))
        job.error_message = result.get("error_message")
        job.completed_at = datetime.now(UTC)

    async def _run_openai_text(self, prompt: str, *, json_response: bool = False) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("OpenAI istemcisi yapılandırılmadı.")
        completion = await self._client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.8,
            messages=[
                {"role": "system", "content": "Türkçe yanıt veren deneyimli bir sosyal medya uzmanısın."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"} if json_response else None,
        )
        content = completion.choices[0].message.content or ""
        usage = completion.usage
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        cost_usd = round(((prompt_tokens + completion_tokens) / 1000) * 0.0015, 6)
        return {
            "content": content,
            "provider": "openai",
            "model": completion.model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": cost_usd,
        }

    def _mock_ideas(self, brand: Brand, platform: str) -> list[dict[str, str]]:
        keywords = [item.strip() for item in (brand.keywords or "").split(",") if item.strip()] or [brand.sector]
        formats = ["resim", "video", "hikaye", "reels", "carousel"]
        ideas = []
        for index in range(5):
            topic = keywords[index % len(keywords)]
            ideas.append(
                {
                    "title": f"{brand.name} için {topic} odaklı içerik fikri {index + 1}",
                    "description": f"{brand.target_audience} kitlesine hitap eden, {brand.tone_of_voice.lower()} tonda {platform} paylaşımı.",
                    "suggested_format": formats[index % len(formats)],
                }
            )
        return ideas

    def _mock_post(self, brand: Brand, idea: str, platform: str) -> str:
        cta = "Sizce bu konuda en önemli detay nedir? Yorumlarda bizimle paylaşın."
        return (
            f"{brand.name} olarak {idea.lower()} konusuna odaklanıyoruz. "
            f"{brand.target_audience} için hazırladığımız bu mesajda {brand.tone_of_voice.lower()} bir dil kullanıyoruz. "
            f"{cta}"
        )[: PLATFORM_LIMITS.get(platform, 2200)]

    def _mock_hashtags(self, brand: Brand, topic: str) -> list[str]:
        base_tags = [
            f"#{topic.replace(' ', '').title()}",
            f"#{brand.sector.replace(' ', '').title()}",
            f"#{brand.name.replace(' ', '')}",
            "#SosyalMedya",
            "#DijitalPazarlama",
            "#Marketing",
            "#İçerikÜretimi",
            "#Branding",
            "#Keşfet",
            "#Growth",
            "#Pazarlama",
            "#Business",
            "#Girişimcilik",
            "#Trendler",
            "#ContentCreator",
            "#InstagramTürkiye",
            "#LinkedinTürkiye",
            "#XTürkiye",
            "#SocialMediaTips",
            "#Pixora",
        ]
        return base_tags[:20]

    def _mock_quality(self, content: str) -> dict[str, Any]:
        length_score = min(len(content) / 25, 40)
        cta_score = 25 if "?" in content or "yorum" in content.lower() else 10
        emoji_score = 10 if any(char in content for char in "✨🔥✅🎯") else 5
        score = round(min(length_score + cta_score + emoji_score + 25, 100), 2)
        feedback = []
        if len(content) < 80:
            feedback.append("Metin biraz kısa; mesajınızı güçlendirmek için birkaç detay daha ekleyin.")
        if "yorum" not in content.lower() and "katıl" not in content.lower():
            feedback.append("Etkileşimi artırmak için daha net bir çağrı-eylem ekleyin.")
        if not feedback:
            feedback.append("İçerik hedef kitle açısından dengeli ve paylaşılabilir görünüyor.")
        improved = content if score >= 80 else f"{content}

Siz bu konuda ne düşünüyorsunuz? Görüşlerinizi yorumlarda paylaşın."
        return {"score": score, "feedback": feedback, "improved_version": improved}

    def _mock_image_url(self, prompt: str) -> str:
        digest = hashlib.md5(prompt.encode("utf-8")).hexdigest()[:12]
        return f"https://placehold.co/1024x1024/png?text=Pixora-{digest}"

    async def generate_content_ideas(self, db: AsyncSession, user_id: Any, brand: Brand, platform: str) -> tuple[list[dict[str, str]], str]:
        prompt = CONTENT_IDEAS_PROMPT.format(
            brand_name=brand.name,
            sector=brand.sector,
            tone=brand.tone_of_voice,
            target_audience=brand.target_audience,
            keywords=brand.keywords or "Belirtilmedi",
            platform=platform,
        )
        provider = "openai" if self._client else "mock"
        job = await self._create_job(db, user_id, brand.id, "content_ideas", provider)
        try:
            if self._client:
                raw = await self._run_openai_text(prompt, json_response=True)
                parsed = json.loads(raw["content"])
                ideas = parsed.get("ideas") if isinstance(parsed, dict) else parsed
            else:
                raw = {"provider": "mock", "model": "mock-turkish-ai", "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0}
                ideas = self._mock_ideas(brand, platform)
            result = {**raw, "ideas": ideas}
            await self._finalize_job(job, result)
            return ideas, prompt
        except Exception as exc:
            await self._finalize_job(job, {"provider": provider, "model": None, "cost_usd": 0, "error_message": str(exc)}, success=False)
            if settings.is_development:
                ideas = self._mock_ideas(brand, platform)
                await self._finalize_job(job, {"provider": "mock", "model": "mock-turkish-ai", "ideas": ideas, "cost_usd": 0})
                return ideas, prompt
            raise ApiError("İçerik fikirleri oluşturulamadı.", "AI_SERVICE_ERROR", 502) from exc

    async def generate_post(self, db: AsyncSession, user_id: Any, brand: Brand, platform: str, idea: str) -> tuple[str, str]:
        prompt = POST_PROMPT.format(
            platform=platform,
            brand_name=brand.name,
            tone=brand.tone_of_voice,
            target_audience=brand.target_audience,
            idea=idea,
            max_chars=PLATFORM_LIMITS.get(platform, 2200),
        )
        provider = "openai" if self._client else "mock"
        job = await self._create_job(db, user_id, brand.id, "post_generate", provider)
        try:
            if self._client:
                raw = await self._run_openai_text(prompt)
                content = raw["content"].strip()
            else:
                raw = {"provider": "mock", "model": "mock-turkish-ai", "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0}
                content = self._mock_post(brand, idea, platform)
            await self._finalize_job(job, {**raw, "content": content})
            return content, prompt
        except Exception as exc:
            await self._finalize_job(job, {"provider": provider, "model": None, "cost_usd": 0, "error_message": str(exc)}, success=False)
            if settings.is_development:
                content = self._mock_post(brand, idea, platform)
                await self._finalize_job(job, {"provider": "mock", "model": "mock-turkish-ai", "content": content, "cost_usd": 0})
                return content, prompt
            raise ApiError("Gönderi oluşturulamadı.", "AI_SERVICE_ERROR", 502) from exc

    async def generate_hashtags(self, db: AsyncSession, user_id: Any, brand: Brand, platform: str, topic: str) -> tuple[list[str], str]:
        prompt = HASHTAG_PROMPT.format(platform=platform, topic=topic, sector=brand.sector)
        provider = "openai" if self._client else "mock"
        job = await self._create_job(db, user_id, brand.id, "hashtag_generate", provider)
        try:
            if self._client:
                raw = await self._run_openai_text(prompt)
                hashtags = [line.strip() for line in raw["content"].splitlines() if line.strip()]
            else:
                raw = {"provider": "mock", "model": "mock-turkish-ai", "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0}
                hashtags = self._mock_hashtags(brand, topic)
            await self._finalize_job(job, {**raw, "hashtags": hashtags})
            return hashtags[:20], prompt
        except Exception as exc:
            await self._finalize_job(job, {"provider": provider, "model": None, "cost_usd": 0, "error_message": str(exc)}, success=False)
            if settings.is_development:
                hashtags = self._mock_hashtags(brand, topic)
                await self._finalize_job(job, {"provider": "mock", "model": "mock-turkish-ai", "hashtags": hashtags, "cost_usd": 0})
                return hashtags, prompt
            raise ApiError("Hashtag üretilemedi.", "AI_SERVICE_ERROR", 502) from exc

    async def rewrite_content(
        self, db: AsyncSession, user_id: Any, brand: Brand, platform: str, content: str, instructions: str | None
    ) -> tuple[str, str]:
        prompt = (
            f"Aşağıdaki {platform} gönderisini {brand.tone_of_voice} tonda yeniden yaz. Türkçe yaz. "
            f"Hedef kitle: {brand.target_audience}."
        )
        if instructions:
            prompt += f" Ek yönlendirme: {instructions}."
        prompt += f"

Metin:
{content}"
        provider = "openai" if self._client else "mock"
        job = await self._create_job(db, user_id, brand.id, "content_rewrite", provider)
        try:
            if self._client:
                raw = await self._run_openai_text(prompt)
                rewritten = raw["content"].strip()
            else:
                raw = {"provider": "mock", "model": "mock-turkish-ai", "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0}
                rewritten = f"{content}

{brand.name} için yenilenmiş çağrı: Şimdi sizin görüşlerinizi duymak isteriz!"
            await self._finalize_job(job, {**raw, "content": rewritten})
            return rewritten, prompt
        except Exception as exc:
            await self._finalize_job(job, {"provider": provider, "model": None, "cost_usd": 0, "error_message": str(exc)}, success=False)
            if settings.is_development:
                rewritten = f"{content}

{brand.name} için yenilenmiş çağrı: Şimdi sizin görüşlerinizi duymak isteriz!"
                await self._finalize_job(job, {"provider": "mock", "model": "mock-turkish-ai", "content": rewritten, "cost_usd": 0})
                return rewritten, prompt
            raise ApiError("İçerik yeniden yazılamadı.", "AI_SERVICE_ERROR", 502) from exc

    async def quality_check(self, db: AsyncSession, user_id: Any, brand: Brand, platform: str, content: str) -> tuple[dict[str, Any], str]:
        prompt = (
            f"Aşağıdaki {platform} gönderisini kalite, etkileşim ve marka tonu açısından değerlendir. "
            f"Marka: {brand.name}. Ton: {brand.tone_of_voice}. Hedef kitle: {brand.target_audience}. "
            f"JSON formatında score, feedback ve improved_version alanlarıyla döndür.

{content}"
        )
        provider = "openai" if self._client else "mock"
        job = await self._create_job(db, user_id, brand.id, "quality_check", provider)
        try:
            if self._client:
                raw = await self._run_openai_text(prompt, json_response=True)
                result = json.loads(raw["content"])
            else:
                raw = {"provider": "mock", "model": "mock-turkish-ai", "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0}
                result = self._mock_quality(content)
            await self._finalize_job(job, {**raw, **result})
            return result, prompt
        except Exception as exc:
            await self._finalize_job(job, {"provider": provider, "model": None, "cost_usd": 0, "error_message": str(exc)}, success=False)
            if settings.is_development:
                result = self._mock_quality(content)
                await self._finalize_job(job, {"provider": "mock", "model": "mock-turkish-ai", **result, "cost_usd": 0})
                return result, prompt
            raise ApiError("Kalite kontrolü yapılamadı.", "AI_SERVICE_ERROR", 502) from exc

    async def analytics_report(self, db: AsyncSession, user_id: Any, brand: Brand, summary: dict[str, int | float]) -> str:
        prompt = (
            f"{brand.name} markası için aşağıdaki performans verilerine göre Türkçe bir analiz raporu oluştur. "
            f"Ton: {brand.tone_of_voice}. Hedef kitle: {brand.target_audience}. "
            f"Güçlü yönler, riskler ve 3 öneri ekle. Veriler: {json.dumps(summary, ensure_ascii=False)}"
        )
        provider = "openai" if self._client else "mock"
        job = await self._create_job(db, user_id, brand.id, "analytics_report", provider)
        try:
            if self._client:
                raw = await self._run_openai_text(prompt)
                report = raw["content"].strip()
            else:
                raw = {"provider": "mock", "model": "mock-turkish-ai", "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0}
                report = (
                    f"{brand.name} için mevcut veriler, erişim ve etkileşim tarafında düzenli bir temel olduğunu gösteriyor. "
                    f"Öne çıkan metrikler: erişim {summary.get('total_reach', 0)}, gösterim {summary.get('total_impressions', 0)}, "
                    f"beğeni {summary.get('total_likes', 0)}. Kısa vadede daha fazla yorum odaklı içerik ve net çağrı-eylemler önerilir."
                )
            await self._finalize_job(job, {**raw, "report": report, "summary": summary})
            return report
        except Exception as exc:
            await self._finalize_job(job, {"provider": provider, "model": None, "cost_usd": 0, "error_message": str(exc)}, success=False)
            if settings.is_development:
                report = (
                    f"{brand.name} için veri özeti olumlu. Etkileşim oranını artırmak için soru odaklı içeriklere, "
                    f"daha sık paylaşım planına ve yüksek performans gösteren formatların tekrar kullanımına odaklanın."
                )
                await self._finalize_job(job, {"provider": "mock", "model": "mock-turkish-ai", "report": report, "summary": summary, "cost_usd": 0})
                return report
            raise ApiError("Analitik raporu oluşturulamadı.", "AI_SERVICE_ERROR", 502) from exc

    async def generate_image(self, db: AsyncSession, user_id: Any, brand: Brand, prompt: str, template_type: str | None = None) -> str:
        provider = "openai" if self._client else "mock"
        job = await self._create_job(db, user_id, brand.id, "image_generate", provider)
        try:
            if self._client:
                image = await self._client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024")
                image_url = image.data[0].url or self._mock_image_url(prompt)
                raw = {"provider": "openai", "model": "gpt-image-1", "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.04}
            else:
                raw = {"provider": "mock", "model": "mock-image-engine", "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0}
                image_url = self._mock_image_url(prompt)
            await self._finalize_job(job, {**raw, "image_url": image_url, "template_type": template_type})
            return image_url
        except Exception as exc:
            await self._finalize_job(job, {"provider": provider, "model": None, "cost_usd": 0, "error_message": str(exc)}, success=False)
            if settings.is_development:
                image_url = self._mock_image_url(prompt)
                await self._finalize_job(job, {"provider": "mock", "model": "mock-image-engine", "image_url": image_url, "template_type": template_type, "cost_usd": 0})
                return image_url
            raise ApiError("Görsel oluşturulamadı.", "AI_SERVICE_ERROR", 502) from exc


ai_service = AIService()
