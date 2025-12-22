import { Component, ErrorInfo, ReactNode } from "react";
import { FaExclamationTriangle } from "react-icons/fa";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#060606] text-white flex flex-col items-center justify-center p-8 text-center">
            <div className="w-24 h-24 bg-red-600/10 rounded-full flex items-center justify-center mb-10 border border-red-600/20">
               <FaExclamationTriangle className="text-red-600 text-4xl" />
            </div>
            <h2 className="text-3xl font-black italic mb-4 tracking-tighter">عذراً، حدث خطأ غير متوقع</h2>
            <p className="text-gray-500 max-w-sm mb-12 text-sm font-medium leading-relaxed">
                نواجه مشكلة تقنية في عرض هذه الصفحة. يرجى المحاولة مرة أخرى أو العودة للرئيسية.
            </p>
            <div className="flex flex-col gap-4 w-full max-w-[280px]">
                <button 
                  onClick={() => window.location.reload()} 
                  className="bg-white/5 hover:bg-white/10 text-white font-bold py-4 rounded-2xl transition-all border border-white/5"
                >
                  إعادة تحميل الصفحة
                </button>
                <button 
                  onClick={() => window.location.href = '/'} 
                  className="bg-red-600 hover:bg-red-700 text-white font-bold py-4 rounded-2xl transition-all shadow-xl shadow-red-600/20"
                >
                  العودة للرئيسية
                </button>
            </div>
            {this.state.error && (
              <pre className="mt-8 p-4 bg-black/50 text-red-400 text-left text-xs overflow-auto max-w-full rounded-lg">
                {this.state.error.toString()}
              </pre>
            )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
