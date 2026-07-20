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

        loadingDiv.classList.remove('hidden');
        resultContainer.classList.add('hidden');
        resultPre.textContent = '';
        generateBtn.disabled = true;

        try {
            const response = await fetch('', {
                method: '',
                headers: {
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
