"""옵시디언 그래프 뷰를 흉내내는 pyvis 시각화 유틸.

사용:
    from obsidian_graph import show_obsidian_graph
    show_obsidian_graph(networkx_graph, "g.html")
"""
from __future__ import annotations

import pathlib
from typing import Iterable, Optional

import networkx as nx
from pyvis.network import Network


# 옵시디언 다크 테마 색 (그래프 뷰 기본값에 가깝게)
OBSIDIAN_BG = "#1e1e1e"
OBSIDIAN_FONT = "#dddddd"
OBSIDIAN_EDGE = "#4a4a4a"
OBSIDIAN_DEFAULT_NODE = "#6e7681"

# 노드 타입별 색 팔레트 (옵시디언의 태그별 색칠 흉내)
TYPE_COLORS = {
    "직업": "#7aa2f7",     # 파랑
    "던전": "#f7768e",     # 빨강
    "보스": "#e0af68",     # 주황
    "아이템": "#9ece6a",   # 초록
    "스킬": "#bb9af7",     # 보라
    "스탯": "#7dcfff",     # 청록
}


def _color_for(node_attrs: dict) -> str:
    t = node_attrs.get("type")
    return TYPE_COLORS.get(t, OBSIDIAN_DEFAULT_NODE)


def show_obsidian_graph(
    graph: nx.Graph,
    output_path: str = "obsidian_graph.html",
    height_px: int = 600,
    physics: bool = True,
    notebook: bool = True,
    highlight_focus: Optional[str] = None,
) -> str:
    """networkx 그래프를 옵시디언 그래프 뷰 스타일로 HTML 렌더링.

    - 어두운 배경 + 타입별 색칠 노드
    - force-directed (barnes_hut) physics 로 노드가 둥둥
    - 호버하면 연결된 노드만 강조 (선택 시 highlight)
    - 드래그·줌·검색 메뉴 활성

    Args:
        graph: networkx Graph / DiGraph
        output_path: 저장할 html 경로
        height_px: 그래프 영역 높이 (픽셀)
        physics: 시뮬레이션 켤지
        notebook: 노트북 안 iframe 으로 띄우려면 True
        highlight_focus: 특정 노드 중심으로 1-hop 만 보이게 (None 이면 전체)

    Returns:
        실제 저장된 파일 경로 (절대 경로)
    """
    g_to_draw: nx.Graph
    if highlight_focus and highlight_focus in graph:
        g_to_draw = nx.ego_graph(graph, highlight_focus, radius=1, undirected=True)
    else:
        g_to_draw = graph

    net = Network(
        height=f"{height_px}px",
        width="100%",
        bgcolor=OBSIDIAN_BG,
        font_color=OBSIDIAN_FONT,
        notebook=notebook,
        cdn_resources="in_line",
        directed=isinstance(graph, nx.DiGraph),
        select_menu=True,
        filter_menu=False,
    )

    # 노드 등록
    for node, attrs in g_to_draw.nodes(data=True):
        title_lines = [f"<b>{node}</b>"]
        for k, v in attrs.items():
            title_lines.append(f"{k}: {v}")
        net.add_node(
            n_id=str(node),
            label=str(node),
            title="<br>".join(title_lines),
            color=_color_for(attrs),
            borderWidth=2,
            size=15 + 3 * g_to_draw.degree(node),
            font={"color": OBSIDIAN_FONT, "size": 14},
        )

    # 엣지 등록
    for u, v, attrs in g_to_draw.edges(data=True):
        label = attrs.get("relation", "")
        net.add_edge(
            source=str(u),
            to=str(v),
            label=label,
            color=OBSIDIAN_EDGE,
            arrows="to" if isinstance(graph, nx.DiGraph) else "",
            font={"color": OBSIDIAN_FONT, "size": 10, "align": "middle"},
            smooth={"type": "continuous"},
        )

    # 옵시디언 그래프 뷰 흉내내는 physics 옵션
    net.set_options("""
    {
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "selectConnectedEdges": true,
        "hoverConnectedEdges": true,
        "navigationButtons": false,
        "zoomView": true
      },
      "physics": {
        "enabled": %s,
        "solver": "barnesHut",
        "barnesHut": {
          "gravitationalConstant": -8000,
          "centralGravity": 0.2,
          "springLength": 120,
          "springConstant": 0.04,
          "damping": 0.4
        },
        "stabilization": {"iterations": 200}
      },
      "edges": {
        "smooth": {"type": "continuous"},
        "selectionWidth": 2
      },
      "nodes": {
        "shape": "dot",
        "scaling": {"min": 10, "max": 50}
      }
    }
    """ % ("true" if physics else "false"))

    out = pathlib.Path(output_path).absolute()
    net.write_html(str(out), notebook=notebook, open_browser=False)
    return str(out)


def build_graph_from_triples(
    triples: Iterable[tuple[str, str, str]],
    node_types: Optional[dict[str, str]] = None,
) -> nx.DiGraph:
    """(subject, relation, object) 튜플 목록으로 DiGraph 생성. 데모 편의용."""
    g = nx.DiGraph()
    node_types = node_types or {}
    for s, r, o in triples:
        if s not in g.nodes:
            g.add_node(s, type=node_types.get(s, ""))
        if o not in g.nodes:
            g.add_node(o, type=node_types.get(o, ""))
        g.add_edge(s, o, relation=r)
    return g
