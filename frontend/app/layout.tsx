import './globals.css'

export const metadata = {
  title: 'AutoCurate - AI-Powered Knowledge Feed',
  description: 'Personalized content curation powered by artificial intelligence',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  )
}
