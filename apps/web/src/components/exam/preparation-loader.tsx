"use client";
import { useEffect, useState } from "react";

export function PreparationLoader() {
    const [seconds, setSeconds] = useState(0);
    useEffect(() => {
        const timer = setInterval(() => setSeconds((s) => s + 1), 1000);
        return () => clearInterval(timer);
    }, []);
    return (
        <div className="preparation-loader">
            <div className="loader-heading" role="status">
                <span className="progress-spinner" aria-hidden="true" />
                <strong>Preparing your file…</strong>
            </div>
            <p>
                We’re preparing it to your exam’s specifications. Keep this page
                open.
            </p>
            <p>Photographs usually take around 10 seconds. The first preparation after a service restart can take longer.</p>
            <span className="elapsed">{seconds}s elapsed</span>
            {seconds >= 25 && (
                <p role="status">
                    This is taking a little longer. Your request is still in
                    progress; there’s no need to upload again.
                </p>
            )}
        </div>
    );
}
