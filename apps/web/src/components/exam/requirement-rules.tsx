import type { ExamDetail } from "../../lib/types";
import { photographSpecRows, requirementSpecRows } from "../../lib/spec-format";

export function RequirementRules({ exam }: { exam: ExamDetail }) {
    return (
        <div className="requirement-rules">
            {exam.requirements?.map((requirement, index) => {
                const rows =
                    requirement.requirement_type === "photograph"
                        ? photographSpecRows(exam)
                        : requirementSpecRows(
                              requirement,
                              index,
                              exam.provenance,
                          );
                const labels = {
                    supported: "We prepare this file",
                    partially_supported:
                        "We prepare part of this · further steps needed",
                    guidance_only: "Follow the official instructions",
                    physical_stage: "Complete at the physical stage",
                    not_yet_supported: "We cannot prepare this file yet",
                };
                return (
                    <section
                        key={requirement.requirement_id}
                        className="rule-sheet"
                    >
                        <h2>{requirement.requirement_name}</h2>
                        <p className="rule-support">
                            {labels[requirement.platform_support]}
                        </p>
                        {requirement.applicability && (
                            <p>Applies when: {requirement.applicability}</p>
                        )}
                        {rows.length > 0 && (
                            <dl className="spec-list">
                                {rows.map((row) => (
                                    <div key={row.term}>
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
                        {requirement.content_instructions &&
                            !/^(not_found|unknown|none)$/i.test(
                                requirement.content_instructions,
                            ) && <p>{requirement.content_instructions}</p>}
                        {requirement.submission_method ===
                            "official_live_capture" && (
                            <p>
                                The official portal takes this photograph.
                                Prepare the other supported files here.
                            </p>
                        )}
                        {requirement.rejection_conditions.length > 0 && (
                            <details>
                                <summary>
                                    Published rejection conditions
                                </summary>
                                <ul>
                                    {requirement.rejection_conditions.map(
                                        (text) => (
                                            <li key={text}>{text}</li>
                                        ),
                                    )}
                                </ul>
                            </details>
                        )}
                    </section>
                );
            })}
        </div>
    );
}
