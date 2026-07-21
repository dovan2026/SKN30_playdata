/**
 * 프로젝트 글ego 4대 파이프라인 통합 고도화 그로스 매니저 OS — JavaScript
 */

const BASE_URL = "http://127.0.0.1:8000";

const state = {
    monitoringThreadId: null,
    biographySessionId: `bio_session_${Date.now()}`,
    currentDraftChapter: "",
};

const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initEventListeners();
    checkServerStatus();
});

function initTabs() {
    document.querySelectorAll(".tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const targetTab = btn.dataset.tab;
            document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

            btn.classList.add("active");
            $(`tab-content-${targetTab}`).classList.add("active");
        });
    });
}

function initEventListeners() {
    // 1. 출판 파이프라인
    $("btn-onboard")?.addEventListener("click", handleOnboard);
    $("btn-refresh-monitoring")?.addEventListener("click", handleRefreshMonitoring);
    $("btn-nudge-approve")?.addEventListener("click", () => handleNudgeApproval("approved"));
    $("btn-nudge-reject")?.addEventListener("click", () => handleNudgeApproval("rejected"));

    // 2. 크로스셀링
    $("btn-cross-sell-analyze")?.addEventListener("click", handleCrossSellAnalyze);

    // 3. 자서전 인터뷰어
    $("btn-send-chat")?.addEventListener("click", handleSendChat);
    $("chat-input-text")?.addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleSendChat();
    });
    $("btn-refine-chapter")?.addEventListener("click", handleRefineChapter);

    // 4. 작가 소싱
    $("btn-run-sourcing")?.addEventListener("click", handleRunSourcing);
}

async function checkServerStatus() {
    try {
        const res = await fetch(`${BASE_URL}/`);
        if (res.ok) {
            $("server-status-dot").classList.add("online");
            $("server-status-label").textContent = "글ego 4대 파이프라인 v4.0 가동 중";
        } else {
            throw new Error("서버 응답 오류");
        }
    } catch {
        $("server-status-dot").classList.add("offline");
        $("server-status-label").textContent = "서버 연결 안 됨";
    }
}

// ════════════════════════════════════════════════════════════════════════════
// PIPELINE 1: 글ego 출판 파이프라인 (슬럼프 지수)
// ════════════════════════════════════════════════════════════════════════════

async function handleOnboard() {
    const cohortId = $("cohort-id").value.trim();
    const projectType = $("project-type").value;
    const cohortStart = $("cohort-start").value.trim();
    let authorData;

    try {
        authorData = JSON.parse($("author-data").value.trim());
    } catch {
        showToast("error", "❌ JSON 규격 오류", "작가 데이터 JSON을 확인해 주세요.");
        return;
    }

    showLoading("기수 온보딩 및 슬럼프 지수(Burnout Index) 분석 중...");

    try {
        const res = await fetch(`${BASE_URL}/cohort/onboard`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                cohort_id: cohortId,
                project_type: projectType,
                cohort_start_date: cohortStart,
                author_manuscripts: authorData,
            }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "온보딩 실패");

        state.monitoringThreadId = data.thread_id;
        $("session-thread-id").textContent = data.thread_id;
        $("session-cohort-id").textContent = data.cohort_id;
        $("session-card").classList.remove("hidden");

        renderDashboard(data.dashboard_summary);
        await syncMonitoringState(data.thread_id);

        showToast("success", "✅ 슬럼프 모니터링 시작", data.message);
    } catch (err) {
        showToast("error", "❌ 온보딩 실패", err.message);
    } finally {
        hideLoading();
    }
}

async function handleRefreshMonitoring() {
    if (!state.monitoringThreadId) return;
    showLoading("슬럼프 지수 새로고침 중...");
    await syncMonitoringState(state.monitoringThreadId);
    hideLoading();
}

async function syncMonitoringState(threadId) {
    try {
        const res = await fetch(`${BASE_URL}/monitoring/state?thread_id=${threadId}`);
        const data = await res.json();
        if (!res.ok) return;

        renderDashboard(data.dashboard_summary);

        if (data.nudge_draft) {
            $("nudge-draft-display").value = data.nudge_draft;
            showToast("warning", "⚠️ 1:1 케어 넛지 대기 중", `${data.nudge_target_author} 작가님의 슬럼프 넛지 메시지가 생성되었습니다.`);
        }
    } catch (err) {
        console.error(err);
    }
}

async function handleNudgeApproval(action) {
    if (!state.monitoringThreadId) return;
    const msg = $("nudge-draft-display").value.trim();

    showLoading(action === "approved" ? "넛지 메시지 발송 중..." : "거절 처리 중...");
    try {
        const res = await fetch(`${BASE_URL}/monitoring/approve`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                thread_id: state.monitoringThreadId,
                approved_message: msg,
                action,
            }),
        });
        const data = await res.json();
        showToast(action === "approved" ? "success" : "info", action === "approved" ? "✅ 발송 완료" : "❌ 거절됨", data.message);
        if (action === "approved") $("nudge-draft-display").value = "";
    } catch (err) {
        showToast("error", "처리 실패", err.message);
    } finally {
        hideLoading();
    }
}

function renderDashboard(summary) {
    if (!summary || !summary.authors) return;

    $("stats-grid").classList.remove("hidden");
    animateNumber("stat-total", summary.summary.total_authors || 0);
    animateNumber("stat-normal", summary.summary.normal_count || 0);
    animateNumber("stat-stagnant", summary.summary.stagnant_count || 0);
    animateNumber("stat-critical", summary.summary.critical_count || 0);

    $("authors-table-card").classList.remove("hidden");
    const tbody = $("authors-tbody");
    tbody.innerHTML = "";

    summary.authors.forEach((author) => {
        const tr = document.createElement("tr");
        const labelClass = `badge-${author.stagnation_label}`;
        const labelText = { normal: "✅ 순항", stagnant: "⚠️ 주의", critical: "🔴 위험" }[author.stagnation_label] || "—";

        tr.innerHTML = `
            <td><code>${author.author_id}</code></td>
            <td>${author.total_chars.toLocaleString()}자</td>
            <td>${author.last_week_delta.toLocaleString()}자</td>
            <td>${author.stagnation_days}일</td>
            <td><strong style="color:${author.burnout_score >= 65 ? '#ff5252' : '#8da2ff'}">${author.burnout_score || 10}점</strong></td>
            <td>
                <div class="progress-bar"><div class="progress-fill" style="width: ${Math.min(100, author.completion_rate)}%"></div></div>
                ${author.completion_rate}%
            </td>
            <td>₩${(author.estimated_royalty || 0).toLocaleString()}</td>
            <td><span class="status-badge ${labelClass}">${labelText}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// ════════════════════════════════════════════════════════════════════════════
// PIPELINE 2: 모두출판 SaaS 크로스셀링 (Before/After & A/B 카피)
// ════════════════════════════════════════════════════════════════════════════

async function handleCrossSellAnalyze() {
    const text = $("cross-sell-text").value.trim();
    if (!text) return;

    showLoading("Before/After 교정 비교 & A/B 세일즈 카피 분석 중...");

    try {
        const res = await fetch(`${BASE_URL}/cross-sell/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: "user_modu_demo",
                manuscript_text: text,
            }),
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "분석 실패");

        $("cross-sell-result-card").classList.remove("hidden");
        $("cross-sell-score").textContent = data.analysis.error_score;
        $("cross-sell-risk-badge").textContent = `${data.analysis.risk_level.toUpperCase()} RISK`;

        // Before/After Diff 렌더링
        $("diff-before-text").textContent = data.diff_preview.before;
        $("diff-after-text").textContent = data.diff_preview.after;

        // 가변 요금 & 쿠폰 코드
        const pricing = data.pricing_tier;
        $("pricing-tier-name").textContent = pricing.tier_name;
        $("pricing-price").textContent = `₩${pricing.discounted_price.toLocaleString()} (${pricing.discount_rate})`;
        $("coupon-badge").textContent = `쿠폰: ${pricing.discount_code}`;

        // A/B 세일즈 카피 파싱 렌더링
        const abText = data.ab_sales_copies || "";
        const parts = abText.split("## 버전 B");
        const versionA = parts[0]?.replace("## 버전 A (손실 회피형)", "").strip ? parts[0].replace("## 버전 A (손실 회피형)", "").trim() : abText;
        const versionB = parts[1]?.replace("(성과 강조형)", "").trim() || "성과 강조형 카피 준비 완료";

        $("copy-version-a").textContent = versionA;
        $("copy-version-b").textContent = versionB;

        showToast("warning", "⚡ '교정의 신' 비포/애프터 A/B 카피 트리거!", "1:1 문장 비교 프리뷰 및 A/B 세일즈 카피 분석이 완료되었습니다.");
    } catch (err) {
        showToast("error", "분석 실패", err.message);
    } finally {
        hideLoading();
    }
}

// ════════════════════════════════════════════════════════════════════════════
// PIPELINE 3: 모두의 자서전 인터뷰어 & 원고 공동수정
// ════════════════════════════════════════════════════════════════════════════

async function handleSendChat() {
    const input = $("chat-input-text");
    const message = input.value.trim();
    if (!message) return;

    input.value = "";
    appendChatBubble("user", message);

    showLoading("자서전 인터뷰어 AI가 대화 분석 및 꼬리 질문 생성 중...");

    try {
        const res = await fetch(`${BASE_URL}/biography/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: state.biographySessionId,
                user_message: message,
                current_topic: "자서전 인터뷰 진행",
            }),
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "대화 실패");

        appendChatBubble("assistant", data.latest_assistant_reply);

        // 4대 챕터 Progress 바 강조
        const currentChapNum = data.current_chapter_info?.chapter_num || 1;
        for (let i = 1; i <= 4; i++) {
            const stepEl = $(`chap-step-${i}`);
            if (stepEl) {
                if (i === currentChapNum) stepEl.classList.add("active");
                else stepEl.classList.remove("active");
            }
        }

        if (data.is_compiled && data.draft_chapter) {
            state.currentDraftChapter = data.draft_chapter;
            $("compiled-chapter-card").classList.remove("hidden");
            $("timeline-map-content").textContent = data.timeline_map || "인생 타임라인 데이터 수집 완료";
            $("chapter-content-box").textContent = data.draft_chapter;

            showToast("success", "📖 자서전 챕터 원고 집필 완료!", "인터뷰 데이터가 충분히 축적되어 자서전 챕터 에세이가 자동 집필되었습니다.");
        }
    } catch (err) {
        showToast("error", "처리 실패", err.message);
    } finally {
        hideLoading();
    }
}

async function handleRefineChapter() {
    const feedbackInput = $("user-refine-feedback");
    const feedback = feedbackInput.value.trim();
    if (!feedback) {
        showToast("warning", "피드백 누락", "원고에 반영할 수정 피드백 지시사항을 입력하세요.");
        return;
    }

    showLoading("유저 피드백을 반영하여 자서전 원고 공동 수정 중...");

    try {
        const res = await fetch(`${BASE_URL}/biography/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: state.biographySessionId,
                user_message: "원고 수정 요청",
                current_topic: "원고 공동 수정",
                user_feedback: feedback,
            }),
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "수정 실패");

        $("chapter-content-box").textContent = data.draft_chapter;
        feedbackInput.value = "";
        showToast("success", "✨ 원고 공동 수정 완료", "유저 피드백이 반영된 새로운 자서전 챕터 원고가 다듬어졌습니다.");
    } catch (err) {
        showToast("error", "수정 실패", err.message);
    } finally {
        hideLoading();
    }
}

function appendChatBubble(role, content) {
    const container = $("chat-messages");
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role}`;
    bubble.textContent = content;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

// ════════════════════════════════════════════════════════════════════════════
// PIPELINE 4: 다윈의 서재 작가 소싱 (하이브리드 & 기획서)
// ════════════════════════════════════════════════════════════════════════════

async function handleRunSourcing() {
    showLoading("트렌드 지수 분석 & OpenAI 벡터 하이브리드 검색 진행 중...");

    try {
        const res = await fetch(`${BASE_URL}/sourcing/run`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "소싱 실패");

        $("sourcing-result-card").classList.remove("hidden");
        $("sourcing-keyword-display").textContent = `🔥 ${data.target_keyword}`;

        const author = data.selected_author;
        if (author) {
            $("sourcing-author-info").textContent = `${author.author_name} (${author.email}) | 전문분야: ${author.specialty} | past: ${author.past_work_summary}`;
            $("sourcing-match-score").textContent = `하이브리드 매칭: ${author.match_score}%`;
        }

        $("sourcing-email-display").value = data.proposal_and_email;

        showToast("success", "🎯 하이브리드 작가 소싱 완수", `'${data.target_keyword}' 주제에 매칭되는 작가를 발굴하고 출판 제안서 & 5대 추천 목차 기획서를 자동 작성했습니다.`);
    } catch (err) {
        showToast("error", "소싱 실패", err.message);
    } finally {
        hideLoading();
    }
}

function showLoading(text = "처리 중...") {
    $("loading-text").textContent = text;
    $("loading-overlay").classList.remove("hidden");
}

function hideLoading() {
    $("loading-overlay").classList.add("hidden");
}

function showToast(type, title, message, duration = 4500) {
    const container = $("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<div><strong style="display:block;margin-bottom:2px;">${title}</strong>${message}</div>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), duration);
}

function animateNumber(elementId, target) {
    const el = $(elementId);
    if (!el) return;
    const start = parseInt(el.textContent) || 0;
    const diff = target - start;
    const steps = 15;
    let step = 0;
    const timer = setInterval(() => {
        step++;
        el.textContent = Math.round(start + diff * (step / steps));
        if (step >= steps) clearInterval(timer);
    }, 25);
}
