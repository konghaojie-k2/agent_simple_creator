import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl lg:static lg:w-auto lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4">
          <code className="font-mono font-bold">Agent Builder</code>
        </p>
        <div className="fixed bottom-0 left-0 flex h-48 w-full items-end justify-center bg-gradient-to-t from-white via-white lg:static lg:h-auto lg:w-auto lg:bg-none">
          <Link
            href="/login"
            className="rounded-lg bg-primary-600 px-6 py-3 text-white font-medium hover:bg-primary-700 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </div>

      <div className="mt-16 text-center">
        <h1 className="text-4xl font-bold mb-4">Build Your Own AI Agents</h1>
        <p className="text-xl text-gray-600 mb-8">
          Simple Agent Builder with Multi-Provider Support
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          <div className="p-6 border rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Multi-Provider</h3>
            <p className="text-gray-600">Support for DeepSeek, Qwen, OpenAI and more</p>
          </div>
          <div className="p-6 border rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Custom Prompts</h3>
            <p className="text-gray-600">Configure system prompts for your agents</p>
          </div>
          <div className="p-6 border rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Real-time Chat</h3>
            <p className="text-gray-600">Stream responses for interactive conversations</p>
          </div>
        </div>
      </div>
    </main>
  )
}
