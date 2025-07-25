import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function ComponentTestPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Component Test Page
          </h1>
          <Badge variant="secondary">Testing UI Components</Badge>
        </div>

        {/* Button Tests */}
        <Card>
          <CardHeader>
            <CardTitle>Button Components</CardTitle>
            <CardDescription>Testing different button variants and sizes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex flex-wrap gap-4">
                <Button variant="default">Default Button</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="outline">Outline</Button>
                <Button variant="ghost">Ghost</Button>
                <Button variant="link">Link Button</Button>
                <Button variant="destructive">Destructive</Button>
              </div>
              
              <div className="flex flex-wrap gap-4">
                <Button size="sm">Small</Button>
                <Button size="default">Default</Button>
                <Button size="lg">Large</Button>
                <Button size="icon">🎯</Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card Tests */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Sample Card 1</CardTitle>
              <CardDescription>This is a test card with some sample content</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                This card demonstrates the Card component with header, title, description, and content sections.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Sample Card 2</CardTitle>
              <CardDescription>Another test card with different content</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Badge variant="default">Featured</Badge>
                <p className="text-gray-600">
                  Cards can contain various types of content including badges, buttons, and text.
                </p>
                <Button variant="outline" size="sm">Learn More</Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Badge Tests */}
        <Card>
          <CardHeader>
            <CardTitle>Badge Components</CardTitle>
            <CardDescription>Testing different badge variants</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              <Badge variant="default">Default</Badge>
              <Badge variant="secondary">Secondary</Badge>
              <Badge variant="outline">Outline</Badge>
              <Badge variant="destructive">Destructive</Badge>
            </div>
          </CardContent>
        </Card>

        <div className="text-center">
          <Button size="lg">
            🎉 All Components Working!
          </Button>
        </div>
      </div>
    </div>
  )
}
