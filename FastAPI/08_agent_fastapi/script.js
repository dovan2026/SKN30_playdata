document.addEventListener('DOMContentLoaded', () => {
    const topicInput = document.getElementById('topic-input');
    const generateBtn = document.getElementById('generate-btn');
    const loadingDiv = document.getElementById('loading');
    const resultContainer = document.getElementById('result-container');
    const resultPre = document.getElementById('result');

    generateBtn.addEventListener('click', async () => {
        const topic = topicInput.value.trim();
        if (!topic) {
            alert('블로그 주제를 입력해주세요.');
            return;
        }

        // 요청을 보내기 전의 화면 상태
        // 로딩 표시는 보여 주고, 이전 결과는 숨기고 지운 뒤, 중복 클릭 방지를 위한 버튼을 비활성화
        loadingDiv.classList.remove('hidden');
        resultContainer.classList.add('hidden');
        resultPre.textContent = '';
        generateBtn.disabled = true;

        // FastAPI의 POST /langgraph 엔드포인트에 JSON 요청을 보냄
        try {
            const response = await fetch('http://127.0.0.1:8000/langgraph', {
                method: 'POST',
                headers: {
                    // 본문이 JSON임을 서버에 알려 Pydantic이 TopicInput으로 
                    // 올바르게 파싱할 수 있게 함.
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ topic }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '서버에서 오류가 발생했습니다.');
            }

            const result = await response.json();
            resultPre.textContent = result.final_content;
            resultContainer.classList.remove('hidden');
        } catch (error) {
            console.error('Error:', error);
            alert(`콘텐츠 생성 중 오류가 발생했습니다: ${error.message}`);
        } finally {
            loadingDiv.classList.add('hidden');
            generateBtn.disabled = false;
        }
    });
});
