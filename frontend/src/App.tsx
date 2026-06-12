import "./index.css";
import { Github } from "lucide-react";

import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { useState, useEffect } from "react";
import Select, { SingleValue } from "react-select";
import * as Scroll from "react-scroll";

interface ApiResponseGenerate {
    token: string;
    error?: string;
}

function App() {
    interface Mode {
        value: string;
        label: string;
    }
    const MODE_OPTION_LIST = [
        { value: "normal", label: "BOOX Mira Pro" },
        { value: "small", label: "BOOX Mira" },
    ];

    const DEFAULT_IMAGE = "gray.png";
    const API_ENDPOINT = "/panel/api";
    const [mode, setMode] = useState(MODE_OPTION_LIST[0]);
    const [imageSrc, setImageSrc] = useState(DEFAULT_IMAGE);
    const [finish, setFinish] = useState(true);
    const [error, setError] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [log, setLog] = useState<string[]>([]);

    const scroller = Scroll.scroller;
    const Element = Scroll.Element;

    const reqGenerate = async (): Promise<ApiResponseGenerate> => {
        const query = new URLSearchParams({ mode: mode.value });
        const res = await fetch(API_ENDPOINT + "/run?" + query);
        const resJson = (await res.json()) as ApiResponseGenerate;
        if (!res.ok || resJson.error || !resJson.token) {
            console.error(resJson.error);
            throw new Error(`画像生成の開始に失敗しました (${res.status})`);
        }
        return resJson;
    };

    const readImage = async (token: string) => {
        const param = new URLSearchParams({ token: token });
        const res = await fetch(API_ENDPOINT + "/image", {
            method: "POST",
            body: param,
        });
        if (!res.ok || !(res.headers.get("Content-Type") || "").startsWith("image/")) {
            throw new Error("画像の取得に失敗しました");
        }
        const resBlob = await res.blob();
        setImageSrc(URL.createObjectURL(resBlob));
    };

    const generate = async () => {
        setFinish(false);
        setError(false);
        setLog([]);
        setImageSrc(DEFAULT_IMAGE);
        try {
            const res = await reqGenerate();
            await readLog(res.token);
        } catch (e) {
            setError(true);
            setErrorMessage(e instanceof Error ? e.message : "通信に失敗しました");
            console.error(e);
        } finally {
            setFinish(true);
        }
    };

    useEffect(() => {
        scroller.scrollTo("logEnd", {
            smooth: true,
            containerId: "log",
        });
    }, [log, scroller]);

    const readLog = async (token: string) => {
        const decoder = new TextDecoder();
        const param = new URLSearchParams({ token: token });
        const res = await fetch(API_ENDPOINT + "/log", {
            method: "POST",
            body: param,
        });
        if (!res.ok || res.body === null) {
            throw new Error("ログの取得に失敗しました");
        }
        const reader = res.body.getReader();
        for (;;) {
            const { done, value } = await reader.read();
            if (done) {
                break;
            }
            const lines = decoder.decode(value).trimEnd().split(/\n/);
            setLog((old) => old.concat(lines));
        }
        await readImage(token);
    };

    const GenerateButton = () => {
        if (finish) {
            return (
                <button
                    className="w-auto px-4 py-2 bg-blue-600 text-white font-medium rounded-sm hover:bg-blue-700 focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                    type="button"
                    data-testid="button"
                    onClick={generate}
                >
                    生成
                </button>
            );
        } else {
            return (
                <button
                    className="w-auto px-4 py-2 bg-blue-600 text-white font-medium rounded-sm opacity-75 cursor-not-allowed flex items-center"
                    type="button"
                    data-testid="button"
                    disabled
                >
                    <span className="spinner mr-3" role="status" aria-hidden="true" />
                    生成中...
                </button>
            );
        }
    };

    const LogData = () => {
        if (error) {
            return <span>{errorMessage}</span>;
        }
        return log.map((line, index) => (
            <span key={index}>
                {line}
                <br />
            </span>
        ));
    };

    const handleModeChange = (v: Mode | null) => {
        if (v !== null) {
            setMode(v);
        }
    };

    return (
        <div className="text-left">
            <div className="flex flex-col md:flex-row items-center p-3 md:px-4 mb-3 bg-white border-b shadow-xs">
                <h1 className="text-2xl font-light my-0 md:mr-auto">気象パネル画像</h1>
            </div>

            <div className="max-w-7xl mx-auto px-4">
                <div>
                    <div className="w-full">
                        <label htmlFor="mode" className="mr-2">
                            モード:
                        </label>
                        <Select
                            options={MODE_OPTION_LIST}
                            defaultValue={MODE_OPTION_LIST[0]}
                            onChange={(v: SingleValue<Mode>) => handleModeChange(v)}
                            className="mb-2"
                            id="mode"
                        />
                        <GenerateButton />
                    </div>
                </div>

                <div className="mt-4">
                    <h2>ログ</h2>
                    <div className="w-full">
                        <div
                            className="w-full overflow-y-scroll ml-2 shadow-sm p-3 bg-white rounded-sm"
                            style={{ height: "10em" }}
                            data-testid="log"
                            id="log"
                        >
                            <small>
                                <LogData />
                                <Element name="logEnd"></Element>
                            </small>
                        </div>
                    </div>
                </div>

                <div className="mt-5">
                    <h2>生成画像</h2>
                    <div className="w-full">
                        <div className="w-full ml-2 shadow-sm bg-white rounded-sm">
                            <TransformWrapper>
                                <TransformComponent>
                                    <img
                                        src={imageSrc}
                                        width="3200"
                                        alt="生成された画像"
                                        data-testid="image"
                                        className="aspect-video max-w-full h-auto rounded-sm"
                                    />
                                </TransformComponent>
                            </TransformWrapper>
                        </div>
                    </div>
                </div>

                <div className="mt-2">
                    <div className="p-1 float-right text-right">
                        <p className="text-2xl">
                            <a
                                href="https://github.com/kimata/e-ink_weather_panel/"
                                className="text-gray-500 hover:text-gray-700 transition-colors"
                            >
                                <Github />
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;
