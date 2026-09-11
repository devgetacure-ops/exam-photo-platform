import type { ExamDetail, PlatformSupport } from "../../lib/types";
import { photographSpecRows, requirementSpecRows } from "../../lib/spec-format";
import { FileTypeDrawing } from "../euk/doodles";

/**
 * Every file's published rules, one card each.
 *
 * The support state is carried in words and in its own colour, and all five
 * stay distinct (DEC-056): colour is one of the three boundary signals, and a
 * page that drew "we can't prepare this yet" in the same tone as "we prepare
 * this" would be saying something false.
 */

const LABELS: Record<PlatformSupport, string> = {
    supported: "We prepare this file",
    partially_supported: "We prepare part of this · further steps needed",
    guidance_only: "Follow the official instructions",
    physical_stage: "Complete at the physical stage",
    not_yet_supported: "We cannot prepare this file yet",
};

const MEANINGLESS = /^(not_found|unknown|none)$/i;

function meaningful(value?: string | null): string | null {
    return value && !MEANINGLESS.test(value.trim()) ? value : null;
}

export function RequirementRules({ exam }: { exam: ExamDetail }) {
    return (
        <ul className="euk-rule-list">
            {exam.requirements?.map((requirement, index) => {
                const rows =
                    requirement.requirement_type === "photograph"
                        ? photographSpecRows(exam)
                        : requirementSpecRows(requirement, index, exam.provenance);
                const instructions = meaningful(requirement.content_instructions);
                const applies = meaningful(requirement.applicability);
                return (
                    <li key={requirement.requirement_id} className="euk-rule-card">
                        <div className="euk-rule-head">
                            <FileTypeDrawing
                                type={requirement.requirement_type}
                                className="euk-rule-icon"
                            />
                            <div className="min-w-0">
                                <h3 className="euk-rule-name">{requirement.requirement_name}</h3>
                                <p
                                    className={`euk-rule-state euk-rule-state--${requirement.platform_support.replace(/_/g, "-")}`}
                                >
                                    {LABELS[requirement.platform_support]}
                                </p>
                            </div>
                        </div>
                        {applies && (
                            <p className="euk-rule-when">
                                <strong>Applies when:</strong> {applies}
                            </p>
                        )}
                        {rows.length > 0 && (
                            <dl className="euk-measure">
                                {rows.map((row) => (
                                    <div key={row.term} className="euk-measure-cell">
                                        <dt>{row.term}</dt>
                                        <dd>
                                            {row.value}
                                            {row.estimated && (
                                                <abbr title="Platform estimate; not established by an official source">
                                                    {" "}
                                                    est.
                                                </abbr>
                                            )}
                                        </dd>
                                    </div>
                                ))}
                            </dl>
                        )}
                        {instructions && <p className="euk-rule-text">{instructions}</p>}
                        {requirement.submission_method === "official_live_capture" && (
                            <p className="euk-rule-text">
                                The official portal takes this photograph. Prepare
                                the other supported files here.
                            </p>
                        )}
                        {requirement.rejection_conditions.length > 0 && (
                            <div className="euk-rule-rejects">
                                <p className="euk-rule-rejects-title">
                                    Published reasons for rejection
                                </p>
                                <ul>
                                    {requirement.rejection_conditions.map((text) => (
                                        <li key={text}>{text}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </li>
                );
            })}
        </ul>
    );
}
