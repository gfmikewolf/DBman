# base/dashboard/contract/views.py
from bdb import effective
from datetime import date
from typing import Iterable, Any

from flask import abort, render_template, url_for, redirect
from werkzeug.wrappers import Response

from sqlalchemy import inspect, select

from app.base.auth.privilege import Privilege, require_privilege
from app.base.crud.utils import fetch_related_objects, fetch_tablename_url_name, get_viewable_instance, get_viewable_instance
from app.database.contract.dbmodels import ClauseScope, UserRoleMAPContract
from app.utils.common import _
from app.extensions import db_session, Base
from app.database.contract.types import ClauseAction, ClauseType
from app.database.contract import Contract

_default_viewer = 'base.dashboard.simple_viewer'
_right_frame = 'right-frame'
_uid = 0

def view_list(instances: Iterable[Any], cls_name:str='', mode:str='compact') -> str:
    global _uid
    if not instances:
        return ''
    connectors = {
        'compact': ', ',
        'lines': '<br>',
        'collapse': '<br>'
    }
    if mode not in connectors:
        mode = 'compact'
    connector = connectors[mode]
    vl = ''
    tn = None
    sample = next(iter(instances))
    if mode == 'collapse':
        if isinstance(sample, Base):
            tn = sample.__class__.__tablename__
        vl += (
            f'<a href="#collapse-view-{_uid}" data-bs-toggle="collapse"'
            f' class="dbman-link fw-bold collapse-toggle collapsed"'
            f' aria-expanded="false">'
            f'<span class="icon-plus"><i class="fa-solid fa-chevron-right"></i></span>'
            f'<span class="icon-minus"><i class="fa-solid fa-chevron-down"></i></span>'
            f'{_(tn or cls_name, True)}</a>'
        )
        vl += f'<div class="collapse" id="collapse-view-{_uid}">'
        _uid += 1
    vl += connector.join([get_viewable_instance(inst, _default_viewer, _right_frame) if isinstance(inst, Base) else inst for inst in instances])
    if mode == 'collapse':
        vl += '</div>'
    return vl
    

@require_privilege('viewer')
def view_contracts(contract_id: int | None = None) -> str | Response:
    with db_session() as sess:
        stmt = select(Contract)
        if not Privilege.is_admin():
            role_ids = Privilege.get_session_role_ids()
            stmt = (
                stmt
                .join(UserRoleMAPContract)
                .where(UserRoleMAPContract.user_role_id.in_(role_ids))
                .distinct()
            )
        contracts = sess.scalars(stmt).all()
        if not contracts:
            return redirect(url_for('base.index'))
        data = dict()
        contract = None
        if contract_id is None:
            contract_id = contracts[0].contract_id
            contract = contracts[0]
        else:
            for c in contracts:
                if c.contract_id == contract_id:
                    contract = c
                    break
        if contract is None:
            abort(404)
        data['contracts'] = [
            (
                f'{c}', 
                url_for('base.dashboard.contract.view_contracts', contract_id=c.contract_id),
                contract_id == c.contract_id
            )
            for c in contracts
        ]
        related_objects = fetch_related_objects(contract, sess, _default_viewer)
        scope_reprs: list[str] = []
        for scope in contract.scopes:
            scope_repr = get_viewable_instance(scope, viewer=_default_viewer, target=_right_frame)
            scope_clauses = sorted(
                [
                    cl 
                    for cl in contract.clauses 
                    if isinstance(cl, ClauseScope)
                    and cl.clause_action in {ClauseAction.A, ClauseAction.U}
                    and cl.new_scope == scope
                ],
                key=lambda cl: cl.clause_effective_date,
                reverse=True
            )
            cs = scope_clauses[0]
            today = date.today()
            effectivedate = cs.clause_effective_date or cs.amendment.amendment_effectivedate
            expirydate = cs.clause_expiry_date or cs.amendment.contract.contract_expirydate
            duration = f' {effectivedate or ''} - {expirydate or ''} '
            if (effectivedate and effectivedate > today) or (expirydate and expirydate < today):
                duration = f' <span class="text-secondary">{cs.effectivedate or ''} - {cs.expirydate or ''}</span> '
            elif expirydate and (expirydate - today).days < 30:
                duration = f' <span class="text-danger">{effectivedate or ''} - {expirydate or ''}</span> '
            scope_repr += duration
            scope_repr += ', '.join(
                [
                    get_viewable_instance(commercial, viewer=_default_viewer, target=_right_frame) 
                    for commercial in contract.commercial_incentives 
                    if commercial.applied_to_scope == scope
                ]
            )
            scope_reprs.append(scope_repr)
        data['contract'] = {
            'name': f'{contract}',
            'fullname': contract.contract_fullname or '',
            'entities': view_list(contract.entities),
            'signdate': contract.contract_signdate,
            'effectivedate': contract.contract_effectivedate,
            'expirydate': contract.contract_expirydate or '',
            'scopes': view_list(scope_reprs, cls_name=_('scope', True), mode='collapse'),
            'contract_number_huawei': contract.contract_number_huawei or '',
            'related_objects': related_objects
        }
        return render_template(
            'dashboard/contract-viewer.jinja',
            data=data
        )

@require_privilege('viewer')
def frame_gantt_charts() -> str:
    return ''

@require_privilege('viewer')
def frame_gantt(contract_id: str) -> str:
    from app.database.contract.dbmodels import Contract
    with db_session() as sess:
        try:
            c0 = sess.get(Contract, int(contract_id))
        except:
            abort(404)
        if not c0:
            abort(404)
        contracts = [c0] + list(c0.child_contracts)

        rows = [
            (c, c.contract_effectivedate, c.contract_expirydate)
            for c in contracts
            if c.contract_effectivedate and c.contract_expirydate
        ]
        if not rows:
            return f'<p>{_('effectivate_date or expiry_date missing')}</p>'

        # 计算时间范围，拉伸到当年1月1日——当年12月31日
        dates = [d for _, s, e in rows for d in (s, e)]
        min_year = min(d.year for d in dates)
        max_year = max(d.year for d in dates)
        min_d = date(min_year, 1, 1)
        max_d = date(max_year, 12, 31)
        total_days = (max_d - min_d).days or 1

        # 动态计算左侧留白：基于最长合同名称长度
        left_margin0 = 5
        max_name_len = left_margin0 + max(len(c.contract_name) for c, _, _ in rows)
        char_width = 8        # 单字符平均宽度（px），可根据实际字体微调
        text_padding = 20      # 额外空白
        margin = max_name_len * char_width + text_padding

        # 布局参数
        chart_width = 800
        chart_height = 30 * len(rows) + 40
        bar_height = 20
        scale_x = chart_width / total_days

        # 开始构造 SVG，外层用一个左对齐的 div 包裹
        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{margin + chart_width + 20}" height="{chart_height}" '
            f'preserveAspectRatio="xMinYMin meet" '
            f'style="display:block; margin:0;">'
        ]
        # 画每行条形和合同名称
        for i, (c, start, end) in enumerate(rows):
            y = 20 + i * 30
            w = (max_d - min_d).days * scale_x
            # 条形
            svg.append(
                f'<rect x="{margin}" y="{y}" width="{w}" height="{bar_height}" '
                f'fill="orange" />'
            )
            # 合同名称
            url = url_for('base.crud.view_record', table_name=c.__tablename__, pks=c.contract_id)
            svg.append(
                f'<a xlink:href="{url}" target="_blank">'
                f'<text x="{left_margin0}" y="{y + bar_height/2 + 4}" '
                f'font-size="16" fill="black">{c.contract_name}</text>'
                f'</a>'
            )
            # 在条形内部为每个 amendment 添加链接和标记
            for am in c.amendments:
                ad = am.amendment_effectivedate
                if not ad:
                    continue
                ax = margin + (ad - min_d).days * scale_x
                ay = y + bar_height/2
                url = url = url_for('base.crud.view_record', 
                                    table_name=am.__tablename__, 
                                    pks=am.amendment_id)
                # 红点并包裹链接，title 显示日期
                clauses_str = '<br>'.join(['* '+_(str(cl), True) for cl in am.clauses])
                remarks = '※ ' if am.amendment_remarks else ''
                remarks += am.amendment_remarks or ''
                svg.append(
                    f'<a xlink:href="{url}" target="_blank">'
                    f'<circle cx="{ax}" cy="{ay}" r="6" fill="red" '
                    f'data-bs-toggle="tooltip" data-bs-html="true" data-bs-custom-class="left-tooltip" '
                    f'title="<span><strong>{am.amendment_name}</strong><br>'
                    f'@{ad.isoformat()}<br>'
                    f'{clauses_str}<br>'
                    f'{remarks}</span>"/>'
                    f'</a>'
                )
        # 在每个新年（除第一个年初）处画一条贯穿全图的虚线，并在顶部写上年份
        for y in range(min_year, max_year+1):
            boundary = date(y, 1, 1)
            x = margin + (boundary - min_d).days * scale_x
            if y != min_year:
                svg.append(
                    f'<line x1="{x}" y1="0" x2="{x}" y2="{chart_height}" '
                    f'stroke="gray" stroke-dasharray="4 4"/>'
                )
            # 年份标签，显示在分隔线顶部
            svg.append(
                f'<text x="{x + 17}" y="12" font-size="12" fill="gray">'
                f'{y}</text>'
            )
        svg.append('</svg>')
        data = ''.join(svg)
        title = 'Frame Contract Gantt Chart'
        return render_template('dashboard.jinja', title=title, data=data)
