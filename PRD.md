# Product Requirements Document: AI Video Clipper

**Version:** 1.0
**Date:** November 2025
**Status:** MVP Development

---

## 1. Executive Summary

### 1.1 Problem Statement

Content creators spend **3-5 hours editing each video**, with 80% of that time spent on repetitive tasks:
- Removing silent pauses
- Finding key moments
- Creating highlights for social media
- Adding subtitles/transcriptions

### 1.2 Solution

AI Video Clipper is a web application that automatically:
- Transcribes video with timestamps
- Removes silence and pauses
- Finds highlights based on keywords
- Generates clips ready for export

**From 3 hours of manual editing to 10 minutes of review.**

### 1.3 Target Audience

**Primary:**
- YouTube creators (1K-100K subscribers)
- Podcasters
- Educational content creators
- Live streamers

**Secondary:**
- Marketing teams
- Course creators
- Social media managers

### 1.4 Unique Value Proposition

"Professional video editing automation at $19/month - 10x faster than manual editing"

**Key Differentiators:**
1. **Speed**: Process 30-min video in <5 minutes
2. **Price**: $19/month vs competitors' $24-40
3. **Simplicity**: 5-minute onboarding, intuitive UI
4. **Focus**: Specialized in highlights, not a bloated all-in-one tool

---

## 2. Success Metrics

### 2.1 Launch Metrics (First 3 Months)

| Metric | Month 1 | Month 3 | Goal |
|--------|---------|---------|------|
| Signups | 100 | 500 | 1,000 |
| Paid Users | 5 | 25 | 50 |
| Conversion Rate | 5% | 5% | 5% |
| Monthly Recurring Revenue | $100 | $500 | $1,000 |
| Videos Processed | 50 | 250 | 500 |
| User Retention (30d) | 40% | 50% | 60% |

### 2.2 Key Performance Indicators

**Product Metrics:**
- Processing time: <5 min for 30-min video (target: <3 min)
- Transcription accuracy: >90% (target: >95%)
- Export success rate: >95%
- Page load time: <2 seconds

**Business Metrics:**
- Customer Acquisition Cost (CAC): <$50
- Lifetime Value (LTV): >$150
- LTV:CAC Ratio: >3:1
- Churn Rate: <10% monthly
- Net Promoter Score (NPS): >40

**Engagement Metrics:**
- Videos per user per month: >2
- % of users who complete onboarding: >60%
- % of users who export a video: >50%
- Average session duration: >15 minutes

---

## 3. Features & Requirements

### 3.1 MoSCoW Prioritization

#### MUST HAVE (MVP - Week 1-12)

**1. User Authentication**
- Email/password registration
- Google OAuth login
- Password reset functionality
- JWT-based sessions

**2. Video Upload**
- Supported formats: MP4, MOV, AVI, WebM
- Maximum file size: 2GB
- Drag-and-drop interface
- Direct upload to S3 via presigned URLs
- Upload progress indicator

**3. Automatic Transcription**
- Speech-to-text with timestamps
- Word-level precision
- Languages: English, Russian, Spanish, German, French
- Accuracy: >90%
- Export transcript as SRT/VTT

**4. Silence Removal**
- Automatic detection of silent segments (>1 second)
- Configurable threshold (-40dB default)
- Preview before/after
- One-click application
- Adjustable minimum silence duration

**5. Keyword Search & Clipping**
- Search transcript for keywords
- Highlight matching segments
- Create clips from keyword matches
- Include context (±5 seconds)
- Multiple keyword support

**6. Timeline Editor**
- Visual timeline with waveform
- Transcript synchronized with video
- Click transcript to seek video
- Trim start/end points
- Select/deselect segments
- Reorder clips

**7. Video Export**
- Resolution options: 720p, 1080p
- Format: MP4 (H.264)
- Quality presets: High, Medium, Low
- Export individual clips or combined video
- Download to local machine
- Progress tracking for exports

**8. Dashboard**
- List all uploaded videos
- Video metadata (duration, size, date)
- Processing status
- Quick actions (view, edit, delete)

#### SHOULD HAVE (Post-MVP - Month 4-6)

**9. Auto-Highlight Detection**
- AI scoring of segments (0-100)
- Based on: audio energy, scene changes, keywords
- "Best moments" suggestions
- Configurable sensitivity

**10. Batch Processing**
- Upload multiple videos
- Apply same settings to all
- Queue management
- Bulk export

**11. Embedded Subtitles**
- Burn subtitles into video
- Customizable styling (font, size, color, position)
- Multiple language support
- Auto-translate (Google Translate API)

**12. Social Media Templates**
- Presets: YouTube Shorts, TikTok, Instagram Reels
- Automatic aspect ratio (9:16)
- Duration limits (15s, 30s, 60s)
- Auto-add captions

**13. Team Collaboration**
- Share videos with team members
- Role-based permissions (viewer, editor, admin)
- Comments on timeline
- Version history

**14. Advanced Editor**
- Multiple video tracks
- Add images/overlays
- Simple transitions
- Background music

#### COULD HAVE (Future - Month 7+)

**15. Live Stream Processing**
- Process Twitch/YouTube streams
- Auto-create highlights during stream
- Post-stream compilation

**16. AI Chapter Generation**
- Automatic video segmentation
- Chapter titles from content
- YouTube chapter export

**17. Mobile Apps**
- iOS/Android native apps
- Mobile-optimized editor
- Push notifications

**18. API Access**
- REST API for integrations
- Webhook notifications
- Zapier integration

#### WON'T HAVE (Out of Scope)

- Advanced VFX (motion graphics, 3D)
- Color grading tools
- Audio mixing (multi-track DAW)
- Screen recording
- Live streaming output

---

## 4. User Flows

### 4.1 First-Time User Journey

```
1. Landing Page
   ↓ "Get Started Free"
2. Sign Up (Google OAuth / Email)
   ↓
3. Welcome Screen (30-second intro)
   ↓
4. Upload First Video
   ↓ Drag & drop
5. Processing (2-5 minutes)
   - Transcription
   - Scene detection
   ↓
6. Editor View
   - Video player (left)
   - Transcript (right)
   - Timeline (bottom)
   ↓
7. Try Features (Guided Tour)
   A. "Remove Silence" → Preview → Apply
   B. "Find Keywords" → Enter word → See matches
   C. "Export" → Select quality → Download
   ↓
8. First Export Success! 🎉
   ↓
9. Upgrade Prompt (if free tier limit reached)
```

### 4.2 Core User Flow: Keyword Clipping

```
1. Dashboard → Select Video
   ↓
2. Editor → Transcript loaded
   ↓
3. Keyword Search Box → Enter "important", "key point"
   ↓
4. Results → 5 matches highlighted
   ↓
5. Select matches → Preview each
   ↓
6. Create Clips → Auto-trimmed with ±5s context
   ↓
7. Review in Timeline → Adjust if needed
   ↓
8. Export → "Export as separate clips" → 720p
   ↓
9. Download ZIP → 5 MP4 files ready
```

### 4.3 Core User Flow: Silence Removal

```
1. Editor → Video loaded with transcript
   ↓
2. "Remove Silence" button
   ↓
3. Settings Modal
   - Threshold: -40dB (slider)
   - Min duration: 1.0s (input)
   - Preview: Before/After side-by-side
   ↓
4. "Apply" → Processing (30 seconds)
   ↓
5. Timeline updated → Silent parts removed
   ↓
6. Review → Play through
   ↓
7. Export → Download clean video
```

---

## 5. Technical Requirements

### 5.1 Performance

| Metric | Target | Maximum |
|--------|--------|---------|
| Upload speed (500MB) | <30s | <60s |
| Transcription (30-min video) | <3 min | <5 min |
| Silence removal (30-min video) | <30s | <60s |
| Export (30-min video, 1080p) | <10 min | <15 min |
| Page load time | <1s | <2s |
| Time to Interactive (TTI) | <2s | <3s |

### 5.2 Scalability

**MVP (Month 1-3):**
- 100 concurrent users
- 500 videos/month
- 50 GB storage
- 500 GB bandwidth

**Year 1:**
- 1,000 concurrent users
- 10,000 videos/month
- 5 TB storage
- 50 TB bandwidth

**Architecture must support:**
- Horizontal scaling (add more workers)
- CDN for video delivery
- Database read replicas
- Queue-based processing

### 5.3 Reliability

- **Uptime**: 99.5% (MVP), 99.9% (production)
- **Data durability**: 99.999999999% (S3 eleven nines)
- **Backup**: Daily database backups, 30-day retention
- **Disaster recovery**: RTO <4 hours, RPO <1 hour

### 5.4 Security

**Authentication & Authorization:**
- JWT tokens with 30-minute expiration
- Refresh tokens (30 days)
- Password hashing (bcrypt)
- OAuth 2.0 (Google)

**Data Protection:**
- HTTPS only (TLS 1.3)
- S3 bucket encryption (AES-256)
- Database encryption at rest
- Secure credential storage (AWS Secrets Manager)

**Rate Limiting:**
- Uploads: 5 per hour per user
- API calls: 100 per minute per user
- Exports: 10 per hour per user

**Compliance:**
- GDPR (EU): User data rights, consent, breach notification
- CCPA (California): Privacy policy, "Do Not Sell" link
- DMCA: Designated agent, takedown process

### 5.5 Browser Support

**Desktop:**
- Chrome 100+ (primary)
- Firefox 100+
- Safari 15+
- Edge 100+

**Mobile:**
- iOS Safari 15+
- Chrome Android 100+

**Not supported:**
- Internet Explorer
- Browsers without ES2020 support

---

## 6. UI/UX Requirements

### 6.1 Design Principles

1. **Speed First**: Every action should feel instant
2. **Clear Feedback**: Always show loading, progress, success, errors
3. **Undo/Redo**: Support for timeline actions
4. **Keyboard Shortcuts**: Power user features
5. **Accessibility**: WCAG 2.1 AA compliance

### 6.2 Key Screens

**1. Landing Page**
- Hero: "AI-Powered Video Editing in Minutes"
- Demo video (30 seconds)
- Feature highlights (3 columns)
- Pricing table
- CTA: "Start Free Trial"

**2. Dashboard**
- Left sidebar: Navigation (Videos, Settings, Billing)
- Main area: Video grid (thumbnails, metadata)
- Top bar: Search, Upload button, User menu
- Empty state: "Upload your first video"

**3. Editor**
- Layout: Resizable panels
  - Left: Video player (50%)
  - Right: Transcript (25%)
  - Bottom: Timeline (25%)
- Top toolbar: Save, Export, Undo/Redo
- Floating action buttons: Remove Silence, Find Keywords

**4. Processing**
- Progress bar with percentage
- Status messages: "Uploading...", "Transcribing...", "Done!"
- Cancel button
- Estimated time remaining

### 6.3 Component Library

**Use Shadcn/ui for:**
- Buttons (primary, secondary, ghost)
- Dialogs (modals)
- Dropdowns (selects)
- Inputs (text, number, slider)
- Tables
- Tabs
- Toast notifications
- Tooltips

**Custom components:**
- VideoPlayer (Video.js wrapper)
- Timeline (React-Konva)
- Waveform (Wavesurfer.js)
- TranscriptViewer (custom)

### 6.4 Accessibility

- [ ] Keyboard navigation (Tab, Enter, Esc)
- [ ] Screen reader support (ARIA labels)
- [ ] Focus indicators
- [ ] Color contrast ratio >4.5:1
- [ ] Video player keyboard shortcuts (Space, Arrow keys)
- [ ] Alt text for images

---

## 7. Monetization & Pricing

### 7.1 Pricing Tiers

| Tier | Price/Month | Videos/Month | Minutes/Month | Storage | Features |
|------|-------------|--------------|---------------|---------|----------|
| **Free** | $0 | 3 | 30 | 1 GB | Basic editing, 720p export |
| **Creator** | $19 | 20 | 150 | 10 GB | All features, 1080p, priority processing |
| **Pro** | $39 | 50 | 400 | 50 GB | API access, batch processing, team (3) |
| **Business** | $99 | Unlimited | 1,000 | 200 GB | White-label, team (10), dedicated support |

**Add-ons:**
- Extra minutes: $0.15/min
- Extra storage: $5/50 GB
- Team members: $15/user/month

### 7.2 Free Tier Limits

- 3 videos per month
- 30 minutes total processing time
- 1 GB storage (auto-delete after 30 days)
- 720p export only
- Watermark on exports
- Standard processing queue (slower)

**Upgrade prompts:**
- After 3rd video: "You've reached your limit"
- When exceeding 10 minutes: "Upgrade for longer videos"
- When selecting 1080p: "High quality exports are Pro-only"

### 7.3 Payment Processing

- **Provider**: Stripe
- **Currencies**: USD (primary), EUR, GBP
- **Payment methods**: Credit/debit card, PayPal
- **Billing**: Monthly or annual (15% discount)
- **Trials**: 7-day free trial (credit card required)
- **Refunds**: 30-day money-back guarantee

---

## 8. Competitive Analysis

| Feature | AI Video Clipper | Descript | Opus Clip | Kapwing |
|---------|------------------|----------|-----------|---------|
| **Price** | $19/mo | $24/mo | $29/mo | $24/mo |
| **Transcription** | ✅ | ✅ | ✅ | ✅ |
| **Auto-highlights** | ✅ | ❌ | ✅ | ❌ |
| **Silence removal** | ✅ | ✅ | ❌ | ✅ |
| **Timeline editor** | ✅ | ✅ (advanced) | ❌ (basic) | ✅ |
| **Processing speed** | 5x | 3x | 10x | 4x |
| **Learning curve** | Low | Medium | Low | Medium |
| **Unique feature** | Keyword clipping | Overdub (voice clone) | Virality score | Collaboration |

**Our competitive advantages:**
1. **Best price-to-value ratio**: $19 for all core features
2. **Fastest onboarding**: 5 minutes to first export
3. **Specialized**: Focus on one thing, do it well
4. **Keyword-based clipping**: Unique approach

---

## 9. Release Plan

### 9.1 Milestones

**Phase 1: Foundation (Weeks 1-4)**
- [x] Project setup (backend, frontend, infra)
- [ ] User authentication (JWT, OAuth)
- [ ] Video upload to S3
- [ ] Database schema
- [ ] Basic UI (Dashboard, Upload)

**Phase 2: Core Processing (Weeks 5-8)**
- [ ] Whisper API integration
- [ ] Background job queue (ARQ)
- [ ] Transcript viewer
- [ ] Silence removal
- [ ] Keyword search

**Phase 3: Editor (Weeks 9-12)**
- [ ] Timeline component
- [ ] Video player with sync
- [ ] Clip selection
- [ ] Trim/edit controls
- [ ] Export functionality

**Phase 4: Polish (Weeks 13-16)**
- [ ] UI/UX improvements
- [ ] Performance optimization
- [ ] Error handling
- [ ] Onboarding flow
- [ ] Help documentation

**Phase 5: Testing (Week 17)**
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] E2E tests
- [ ] Load testing
- [ ] Security audit

**Phase 6: Beta Launch (Week 18)**
- [ ] Private beta (50 users)
- [ ] Feedback collection
- [ ] Bug fixes
- [ ] Soft launch

**Phase 7: Public Launch (Week 19-20)**
- [ ] Product Hunt submission
- [ ] Marketing campaign
- [ ] Monitor metrics
- [ ] Rapid iteration

**Total Timeline: 20 weeks (~5 months)**

### 9.2 Success Criteria for Launch

**Must achieve before public launch:**
- [ ] 50 beta users tested successfully
- [ ] <5% error rate on processing
- [ ] <2 second page load time
- [ ] 99% uptime during beta
- [ ] Stripe integration working
- [ ] All MUST-HAVE features complete
- [ ] Security audit passed
- [ ] Legal compliance (GDPR, CCPA, DMCA)

---

## 10. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **High API costs** | High | Medium | Start with Whisper API, plan migration to self-hosted |
| **Poor transcription accuracy** | High | Low | Use industry-leading Whisper, allow manual corrections |
| **Slow processing** | High | Medium | Optimize code, use GPU workers, parallel processing |
| **Storage costs** | Medium | High | Auto-delete old files, lifecycle policies (S3 Glacier) |
| **User churn** | High | Medium | Focus on onboarding, add value quickly, collect feedback |
| **Copyright issues** | High | Low | DMCA compliance, user agreement, content moderation |
| **Competition** | Medium | High | Move fast, differentiate with keywords, better UX |
| **Technical debt** | Medium | Medium | Write tests, code reviews, refactor regularly |

---

## 11. Out of Scope (v1)

**Explicitly NOT included in MVP:**
- Mobile applications (iOS/Android)
- Advanced video effects (VFX, transitions)
- Audio mixing/mastering
- Live streaming
- Desktop applications
- Browser extensions
- API for third-party integrations
- White-labeling
- Multi-language UI (English only)
- Collaboration features (comments, permissions)

**Post-MVP features to consider:**
- Auto-translate subtitles
- AI voice-over generation
- Video SEO optimization (titles, descriptions)
- Social media auto-posting
- Analytics dashboard (video performance)

---

## 12. Appendix

### 12.1 Technical Stack Summary

**Backend:**
- Python 3.11+ with FastAPI
- PostgreSQL 15 (data)
- Redis 7 (cache + queue)
- ARQ (async workers)
- SQLModel (ORM)
- Alembic (migrations)

**Frontend:**
- Next.js 14 (App Router)
- React 18
- TypeScript
- Shadcn/ui (Radix + Tailwind)
- Remotion (video composition)
- React-Konva (timeline)
- Wavesurfer.js (audio viz)

**Infrastructure:**
- Docker + Docker Compose
- AWS S3 (storage)
- AWS CloudFront (CDN)
- AWS EC2/ECS (compute)
- GitHub Actions (CI/CD)

**AI/ML:**
- OpenAI Whisper API (transcription)
- PySceneDetect (scene detection)
- audio-slicer (silence removal)
- YOLOv8 (optional object detection)

### 12.2 Cost Estimates

**Per 100 hours of video processing:**
- Transcription (Whisper API): $36
- Compute (workers): $30-50
- Storage (S3): $10-20
- Bandwidth (CloudFront): $10-20
- **Total: ~$86-126/100 hours**

**Break-even: 25-30 paid users at $19/month**

### 12.3 Market Size

- **Total Addressable Market (TAM)**: $9.3B by 2030
- **Serviceable Available Market (SAM)**: ~10M content creators
- **Serviceable Obtainable Market (SOM)**: 10K users (Year 1)

### 12.4 References

- OpenAI Whisper API Pricing: https://openai.com/pricing
- AWS S3 Pricing: https://aws.amazon.com/s3/pricing/
- Competitor analysis: Descript, Opus Clip, Kapwing, Runway ML
- Market research: Grand View Research, Statista

---

**Document Status:** ✅ Approved for Development
**Last Updated:** November 7, 2025
**Next Review:** After Beta Launch (Week 18)
